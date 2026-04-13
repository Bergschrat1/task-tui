package tui

import (
	"fmt"
	"sort"

	"task-tui/internal/taskwarrior"

	"charm.land/bubbles/v2/key"
	tea "charm.land/bubbletea/v2"
	"charm.land/lipgloss/v2"
	ltable "charm.land/lipgloss/v2/table"
	"charm.land/log/v2"
)

type projectAggregate struct {
	total     int
	pending   int
	completed int
	urgency   float64
}

type projectsModel struct {
	labels  []string
	rowData [][]string
	cur     cursorState
	cli     *taskwarrior.TaskCli
	width   int
	height  int
}

func newProjectsModel(cli *taskwarrior.TaskCli) projectsModel {
	return projectsModel{
		labels: []string{"Project", "Remaining", "Completed", "Urgency"},
		cli:    cli,
	}
}

type projectRefreshMsg struct {
	tasks []taskwarrior.Task
	err   error
}

func (m projectsModel) refreshCmd() tea.Cmd {
	return func() tea.Msg {
		tasks, err := m.cli.ExportAllTasks()
		if err != nil {
			return projectRefreshMsg{err: err}
		}
		return projectRefreshMsg{tasks: tasks}
	}
}

func (m projectsModel) Update(msg tea.Msg) (projectsModel, tea.Cmd) {
	switch msg := msg.(type) {
	case projectRefreshMsg:
		if msg.err != nil {
			log.Error("project refresh failed", "err", msg.err)
			return m, nil
		}
		m.rebuildTable(msg.tasks)
		log.Info("projects refreshed", "tasks", len(msg.tasks))
		return m, nil

	case tea.KeyPressMsg:
		m.cur.handleKey(msg)
		return m, nil
	}

	return m, nil
}

func (m *projectsModel) rebuildTable(tasks []taskwarrior.Task) {
	agg := make(map[string]*projectAggregate)

	for _, t := range tasks {
		name := "(none)"
		if t.Project != nil {
			name = *t.Project
		}
		if _, ok := agg[name]; !ok {
			agg[name] = &projectAggregate{}
		}
		a := agg[name]
		a.total++
		switch t.Status {
		case taskwarrior.StatusCompleted:
			a.completed++
		case taskwarrior.StatusDeleted:
			// skip
		default:
			a.pending++
			a.urgency += t.Urgency
		}
	}

	// Sort by project name, filter out fully completed
	var names []string
	for name, a := range agg {
		if a.pending > 0 {
			names = append(names, name)
		}
	}
	sort.Strings(names)

	m.rowData = make([][]string, 0, len(names))
	for _, name := range names {
		a := agg[name]
		pct := ""
		if a.total > 0 {
			pct = fmt.Sprintf("%d (%d%%)", a.pending, a.completed*100/a.total)
		}
		m.rowData = append(m.rowData, []string{
			name,
			fmt.Sprintf("%d", a.pending),
			pct,
			fmt.Sprintf("%.1f", a.urgency),
		})
	}

	m.cur.total = len(m.rowData)
	m.cur.clamp()
}

func (m projectsModel) View() string {
	if len(m.rowData) == 0 {
		return "No projects."
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

func (m *projectsModel) SetSize(width, height int) {
	m.width = width
	m.height = height
	m.cur.height = height
}

// projectsKeyMap defines the help key map for the projects tab.
type projectsKeyMap struct{}

func (projectsKeyMap) ShortHelp() []key.Binding {
	return []key.Binding{
		keys.Up, keys.Down, keys.PrevTab, keys.NextTab, keys.Quit,
	}
}

func (projectsKeyMap) FullHelp() [][]key.Binding {
	return [][]key.Binding{
		{keys.Up, keys.Down, keys.PrevTab, keys.NextTab, keys.Quit},
	}
}
