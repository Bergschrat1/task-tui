package tui

import (
	"fmt"
	"strconv"
	"time"

	"task-tui-go/internal/taskwarrior"
	"task-tui-go/internal/util"

	"github.com/charmbracelet/bubbles/table"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// Column formatting functions map column names to display formatters.
var columnFormatters = map[string]func(*taskwarrior.Task) string{
	"id":          func(t *taskwarrior.Task) string { return strconv.Itoa(t.ID) },
	"description": func(t *taskwarrior.Task) string { return t.Description },
	"project":     func(t *taskwarrior.Task) string { return t.ProjectString() },
	"priority":    func(t *taskwarrior.Task) string { return t.PriorityString() },
	"tags":        func(t *taskwarrior.Task) string { return t.TagsString() },
	"status":      func(t *taskwarrior.Task) string { return string(t.Status) },
	"uuid":        func(t *taskwarrior.Task) string { return t.UUID[:8] },
	"urgency":     func(t *taskwarrior.Task) string { return fmt.Sprintf("%.1f", t.Urgency) },
	"due": func(t *taskwarrior.Task) string {
		if t.Due == nil {
			return ""
		}
		tt := t.Due.Time
		return util.FormatVagueDatetime(&tt)
	},
	"entry": func(t *taskwarrior.Task) string {
		tt := t.Entry.Time
		return util.FormatVagueDatetime(&tt)
	},
	"modified": func(t *taskwarrior.Task) string {
		tt := t.Modified.Time
		return util.FormatVagueDatetime(&tt)
	},
	"start": func(t *taskwarrior.Task) string {
		if t.Start == nil {
			return ""
		}
		tt := t.Start.Time
		return util.FormatVagueDatetime(&tt)
	},
	"scheduled": func(t *taskwarrior.Task) string {
		if t.Scheduled == nil {
			return ""
		}
		tt := t.Scheduled.Time
		return util.FormatVagueDatetime(&tt)
	},
	"wait": func(t *taskwarrior.Task) string {
		if t.Wait == nil {
			return ""
		}
		tt := t.Wait.Time
		return util.FormatVagueDatetime(&tt)
	},
	"until": func(t *taskwarrior.Task) string {
		if t.Until == nil {
			return ""
		}
		tt := t.Until.Time
		return util.FormatVagueDatetime(&tt)
	},
	"end": func(t *taskwarrior.Task) string {
		if t.End == nil {
			return ""
		}
		tt := t.End.Time
		return util.FormatVagueDatetime(&tt)
	},
	"recur": func(t *taskwarrior.Task) string {
		if t.Recur == nil {
			return ""
		}
		return *t.Recur
	},
	"depends": func(t *taskwarrior.Task) string {
		if len(t.Depends) == 0 {
			return ""
		}
		return fmt.Sprintf("[%d]", len(t.Depends))
	},
}

type tasksModel struct {
	table     table.Model
	tasks     []taskwarrior.Task
	columns   []string
	labels    []string
	cli       *taskwarrior.TaskCli
	report    string
	width     int
	height    int
	selectID  int // task ID to select after refresh
}

func newTasksModel(cli *taskwarrior.TaskCli, report string) tasksModel {
	t := table.New(
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

	return tasksModel{
		table:  t,
		cli:    cli,
		report: report,
	}
}

// refreshCmd loads tasks from taskwarrior asynchronously.
func (m tasksModel) refreshCmd() tea.Cmd {
	return func() tea.Msg {
		tasks, err := m.cli.ExportTasks(m.report)
		if err != nil {
			return taskRefreshMsg{err: err}
		}
		cols, labels, err := m.cli.GetReportColumns(m.report)
		if err != nil {
			return taskRefreshMsg{err: err}
		}
		return taskRefreshMsg{tasks: tasks, columns: cols, labels: labels}
	}
}

type taskRefreshMsg struct {
	tasks   []taskwarrior.Task
	columns []string
	labels  []string
	err     error
}

func (m tasksModel) Update(msg tea.Msg) (tasksModel, tea.Cmd) {
	switch msg := msg.(type) {
	case taskRefreshMsg:
		if msg.err != nil {
			return m, nil
		}
		m.tasks = msg.tasks
		m.columns = msg.columns
		m.labels = msg.labels
		m.rebuildTable()
		return m, nil

	case tea.KeyMsg:
		var cmd tea.Cmd
		m.table, cmd = m.table.Update(msg)
		return m, cmd
	}

	var cmd tea.Cmd
	m.table, cmd = m.table.Update(msg)
	return m, cmd
}

func (m *tasksModel) rebuildTable() {
	if len(m.columns) == 0 {
		return
	}

	// Build columns with auto-calculated widths
	tableColumns := m.calculateColumns()
	m.table.SetColumns(tableColumns)

	// Build rows
	rows := make([]table.Row, len(m.tasks))
	selectIdx := 0
	for i := range m.tasks {
		row := make(table.Row, len(m.columns))
		for j, col := range m.columns {
			if formatter, ok := columnFormatters[col]; ok {
				row[j] = formatter(&m.tasks[i])
			}
		}
		rows[i] = row
		if m.selectID > 0 && m.tasks[i].ID == m.selectID {
			selectIdx = i
		}
	}

	m.table.SetRows(rows)
	if len(rows) > 0 {
		m.table.SetCursor(selectIdx)
	}
	m.selectID = 0
}

func (m *tasksModel) calculateColumns() []table.Column {
	if len(m.columns) == 0 {
		return nil
	}

	// Calculate max content width per column
	widths := make([]int, len(m.columns))
	for i, label := range m.labels {
		widths[i] = len(label)
	}
	for i := range m.tasks {
		for j, col := range m.columns {
			if formatter, ok := columnFormatters[col]; ok {
				w := len(formatter(&m.tasks[i]))
				if w > widths[j] {
					widths[j] = w
				}
			}
		}
	}

	// Cap column widths, distribute remaining space to description
	available := m.width - 4 // border padding
	totalFixed := 0
	descIdx := -1
	for i, col := range m.columns {
		if col == "description" {
			descIdx = i
			continue
		}
		// Cap non-description columns at their content width + 2 padding
		widths[i] = widths[i] + 2
		if widths[i] > 40 {
			widths[i] = 40
		}
		totalFixed += widths[i]
	}

	if descIdx >= 0 {
		descWidth := available - totalFixed
		if descWidth < 20 {
			descWidth = 20
		}
		widths[descIdx] = descWidth
	}

	cols := make([]table.Column, len(m.columns))
	for i, label := range m.labels {
		cols[i] = table.Column{Title: label, Width: widths[i]}
	}
	return cols
}

func (m tasksModel) View() string {
	return m.table.View()
}

func (m *tasksModel) SetSize(width, height int) {
	m.width = width
	m.height = height
	m.table.SetWidth(width)
	m.table.SetHeight(height - 2) // leave room for footer
	m.rebuildTable()
}

// SelectedTask returns the currently selected task, or nil.
func (m *tasksModel) SelectedTask() *taskwarrior.Task {
	cursor := m.table.Cursor()
	if cursor < 0 || cursor >= len(m.tasks) {
		return nil
	}
	return &m.tasks[cursor]
}

// computeVirtualTags assigns virtual tags to all tasks.
func computeVirtualTags(tasks []taskwarrior.Task, cfg *taskwarrior.Config) {
	today := time.Now().UTC().Truncate(24 * time.Hour)

	// Build UUID lookup for dependency checking
	byUUID := make(map[string]*taskwarrior.Task, len(tasks))
	for i := range tasks {
		byUUID[tasks[i].UUID] = &tasks[i]
	}

	for i := range tasks {
		t := &tasks[i]
		if t.VirtualTags == nil {
			t.VirtualTags = make(map[taskwarrior.VirtualTag]bool)
		}

		if t.Start != nil {
			t.VirtualTags[taskwarrior.VTagActive] = true
		}
		if t.Priority != nil {
			t.VirtualTags[taskwarrior.VTagPriority] = true
		}
		if len(t.Tags) > 0 {
			t.VirtualTags[taskwarrior.VTagTagged] = true
		} else {
			t.VirtualTags[taskwarrior.VTagNoTag] = true
		}
		if t.Scheduled != nil {
			t.VirtualTags[taskwarrior.VTagScheduled] = true
		}
		if t.Until != nil {
			t.VirtualTags[taskwarrior.VTagUntil] = true
		}
		if t.Project == nil {
			t.VirtualTags[taskwarrior.VTagNoProject] = true
		}

		switch t.Status {
		case taskwarrior.StatusWaiting:
			t.VirtualTags[taskwarrior.VTagWaiting] = true
		case taskwarrior.StatusRecurring:
			t.VirtualTags[taskwarrior.VTagRecurring] = true
		case taskwarrior.StatusCompleted:
			t.VirtualTags[taskwarrior.VTagCompleted] = true
		case taskwarrior.StatusDeleted:
			t.VirtualTags[taskwarrior.VTagDeleted] = true
		}

		// Dependency-based tags
		for _, depUUID := range t.Depends {
			dep := byUUID[depUUID]
			if dep == nil {
				continue
			}
			if dep.Status != taskwarrior.StatusCompleted && dep.Status != taskwarrior.StatusDeleted &&
				t.Status != taskwarrior.StatusCompleted && t.Status != taskwarrior.StatusDeleted {
				dep.VirtualTags[taskwarrior.VTagBlocking] = true
				t.VirtualTags[taskwarrior.VTagBlocked] = true
			}
		}

		// Due date tags
		if t.Due != nil {
			dueDate := t.Due.Time.Truncate(24 * time.Hour)
			deltaDays := int(dueDate.Sub(today).Hours() / 24)
			if deltaDays < 0 {
				t.VirtualTags[taskwarrior.VTagOverdue] = true
			} else if deltaDays == 0 {
				t.VirtualTags[taskwarrior.VTagDue] = true
				t.VirtualTags[taskwarrior.VTagDueToday] = true
			} else if deltaDays <= cfg.Due {
				t.VirtualTags[taskwarrior.VTagDue] = true
			}
		}
	}
}
