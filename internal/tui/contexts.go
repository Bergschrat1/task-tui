package tui

import (
	"task-tui/internal/taskwarrior"

	"charm.land/bubbles/v2/table"
	tea "charm.land/bubbletea/v2"
	"charm.land/lipgloss/v2"
	"charm.land/log/v2"
)

type contextsModel struct {
	table    table.Model
	contexts []taskwarrior.ContextInfo
	cli      *taskwarrior.TaskCli
	width    int
	height   int
}

func newContextsModel(cli *taskwarrior.TaskCli) contextsModel {
	cols := []table.Column{
		{Title: "Context", Width: 20},
		{Title: "Filter", Width: 50},
	}

	t := table.New(
		table.WithColumns(cols),
		table.WithFocused(true),
	)

	s := table.DefaultStyles()
	s.Header = s.Header.
		BorderStyle(lipgloss.NormalBorder()).
		BorderForeground(lipgloss.Color("240")).
		BorderBottom(true).
		Bold(true)
	s.Selected = s.Selected.
		Foreground(lipgloss.Color("229")).
		Background(lipgloss.Color("57")).
		Bold(false)
	t.SetStyles(s)

	return contextsModel{
		table: t,
		cli:   cli,
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
		var cmd tea.Cmd
		m.table, cmd = m.table.Update(msg)
		return m, cmd
	}

	var cmd tea.Cmd
	m.table, cmd = m.table.Update(msg)
	return m, cmd
}

func (m *contextsModel) rebuildTable() {
	rows := make([]table.Row, len(m.contexts))
	activeIdx := 0
	for i, ctx := range m.contexts {
		name := ctx.Name
		if ctx.IsActive {
			name += " *"
			activeIdx = i
		}
		rows[i] = table.Row{name, ctx.ReadFilter}
	}
	m.table.SetRows(rows)
	m.table.SetCursor(activeIdx)
}

func (m contextsModel) View() string {
	return m.table.View()
}

func (m *contextsModel) SetSize(width, height int) {
	m.width = width
	m.height = height
	m.table.SetWidth(width)
	m.table.SetHeight(height - 2)

	cols := []table.Column{
		{Title: "Context", Width: 20},
		{Title: "Filter", Width: width - 26},
	}
	m.table.SetColumns(cols)
}

// SelectedContext returns the currently selected context.
func (m *contextsModel) SelectedContext() *taskwarrior.ContextInfo {
	cursor := m.table.Cursor()
	if cursor < 0 || cursor >= len(m.contexts) {
		return nil
	}
	return &m.contexts[cursor]
}
