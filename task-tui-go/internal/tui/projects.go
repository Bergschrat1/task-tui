package tui

import (
	"fmt"
	"sort"

	"task-tui-go/internal/taskwarrior"

	"charm.land/bubbles/v2/table"
	tea "charm.land/bubbletea/v2"
	"charm.land/lipgloss/v2"
	"charm.land/log/v2"
)

type projectAggregate struct {
	total     int
	pending   int
	completed int
	urgency   float64
}

type projectsModel struct {
	table table.Model
	cli   *taskwarrior.TaskCli
	width int
	height int
}

func newProjectsModel(cli *taskwarrior.TaskCli) projectsModel {
	cols := []table.Column{
		{Title: "Project", Width: 30},
		{Title: "Remaining", Width: 12},
		{Title: "Completed", Width: 12},
		{Title: "Urgency", Width: 12},
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

	return projectsModel{
		table: t,
		cli:   cli,
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
		var cmd tea.Cmd
		m.table, cmd = m.table.Update(msg)
		return m, cmd
	}

	var cmd tea.Cmd
	m.table, cmd = m.table.Update(msg)
	return m, cmd
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

	rows := make([]table.Row, 0, len(names))
	for _, name := range names {
		a := agg[name]
		pct := ""
		if a.total > 0 {
			pct = fmt.Sprintf("%d (%d%%)", a.pending, a.completed*100/a.total)
		}
		rows = append(rows, table.Row{
			name,
			fmt.Sprintf("%d", a.pending),
			pct,
			fmt.Sprintf("%.1f", a.urgency),
		})
	}

	m.table.SetRows(rows)
}

func (m projectsModel) View() string {
	return m.table.View()
}

func (m *projectsModel) SetSize(width, height int) {
	m.width = width
	m.height = height
	m.table.SetWidth(width)
	m.table.SetHeight(height - 2)

	// Recalculate column widths
	cols := []table.Column{
		{Title: "Project", Width: width - 42},
		{Title: "Remaining", Width: 12},
		{Title: "Completed", Width: 12},
		{Title: "Urgency", Width: 12},
	}
	m.table.SetColumns(cols)
}
