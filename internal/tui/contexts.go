package tui

import (
	"task-tui/internal/taskwarrior"

	tea "charm.land/bubbletea/v2"
	"charm.land/lipgloss/v2"
	ltable "charm.land/lipgloss/v2/table"
	"charm.land/log/v2"
)

type contextsModel struct {
	labels   []string
	rowData  [][]string
	contexts []taskwarrior.ContextInfo
	cur      cursorState
	cli      *taskwarrior.TaskCli
	width    int
	height   int
}

func newContextsModel(cli *taskwarrior.TaskCli) contextsModel {
	return contextsModel{
		labels: []string{"Context", "Filter"},
		cli:    cli,
	}
}

type contextRefreshMsg struct {
	contexts []taskwarrior.ContextInfo
	err      error
}

type contextSelectedMsg struct {
	context taskwarrior.ContextInfo
}

func (m contextsModel) refreshCmd() tea.Cmd {
	return func() tea.Msg {
		contexts := m.cli.ListContexts()
		return contextRefreshMsg{contexts: contexts}
	}
}

func (m contextsModel) Update(msg tea.Msg) (contextsModel, tea.Cmd) {
	switch msg := msg.(type) {
	case contextRefreshMsg:
		if msg.err != nil {
			log.Error("context refresh failed", "err", msg.err)
			return m, nil
		}
		m.contexts = msg.contexts
		m.rebuildTable()
		log.Info("contexts refreshed", "count", len(m.contexts))
		return m, nil

	case tea.KeyPressMsg:
		m.cur.handleKey(msg)
		return m, nil
	}

	return m, nil
}

func (m *contextsModel) rebuildTable() {
	m.rowData = make([][]string, len(m.contexts))
	activeIdx := 0
	for i, ctx := range m.contexts {
		name := ctx.Name
		if ctx.IsActive {
			name += " *"
			activeIdx = i
		}
		m.rowData[i] = []string{name, ctx.ReadFilter}
	}
	m.cur.total = len(m.rowData)
	m.cur.cursor = activeIdx
	m.cur.clamp()
}

func (m contextsModel) View() string {
	if len(m.rowData) == 0 {
		return "No contexts."
	}

	offset := m.cur.scrollOffset()

	t := ltable.New().
		Headers(m.labels...).
		Rows(m.rowData...).
		Width(m.width).
		Height(m.height - 2).
		YOffset(offset).
		Border(lipgloss.NormalBorder()).
		BorderStyle(lipgloss.NewStyle().Foreground(lipgloss.Color("240"))).
		BorderHeader(true).
		BorderTop(false).
		BorderBottom(false).
		BorderLeft(false).
		BorderRight(false).
		BorderColumn(false).
		BorderRow(false).
		StyleFunc(func(row, col int) lipgloss.Style {
			if row == ltable.HeaderRow {
				return headerStyle
			}
			return lipgloss.NewStyle()
		})

	rendered := m.cur.underlineRow(t.Render())
	return lipgloss.NewStyle().PaddingLeft(1).Render(rendered)
}

func (m *contextsModel) SetSize(width, height int) {
	m.width = width
	m.height = height
	m.cur.height = height
}

// SelectedContext returns the currently selected context.
func (m *contextsModel) SelectedContext() *taskwarrior.ContextInfo {
	if m.cur.cursor < 0 || m.cur.cursor >= len(m.contexts) {
		return nil
	}
	return &m.contexts[m.cur.cursor]
}
