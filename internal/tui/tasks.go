package tui

import (
	"fmt"
	"strconv"
	"time"

	"task-tui/internal/taskwarrior"
	"task-tui/internal/util"

	tea "charm.land/bubbletea/v2"
	"charm.land/lipgloss/v2"
	ltable "charm.land/lipgloss/v2/table"
	"charm.land/log/v2"
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

var headerStyle = lipgloss.NewStyle().Bold(true)

type tasksModel struct {
	tasks     []taskwarrior.Task
	columns   []string
	labels    []string
	rowData   [][]string
	rowStyles []taskwarrior.TaskStyle

	cur      cursorState
	cli      *taskwarrior.TaskCli
	cfg      *taskwarrior.Config
	report   string
	width    int
	height   int
	selectID int
}

func newTasksModel(cli *taskwarrior.TaskCli, cfg *taskwarrior.Config, report string) tasksModel {
	return tasksModel{
		cli:    cli,
		cfg:    cfg,
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
			log.Error("task refresh failed", "err", msg.err)
			return m, nil
		}
		m.tasks = msg.tasks
		m.columns = msg.columns
		m.labels = msg.labels
		m.rebuildTable()
		log.Info("tasks refreshed", "count", len(m.tasks), "columns", len(m.columns))
		return m, nil

	case tea.KeyPressMsg:
		m.cur.handleKey(msg)
		return m, nil
	}

	return m, nil
}

func (m *tasksModel) rebuildTable() {
	if len(m.columns) == 0 {
		return
	}

	// Compute virtual tags for styling
	computeVirtualTags(m.tasks, m.cfg)

	// Build all rows first
	allRows := make([][]string, len(m.tasks))
	selectIdx := 0
	for i := range m.tasks {
		row := make([]string, len(m.columns))
		for j, col := range m.columns {
			if formatter, ok := columnFormatters[col]; ok {
				row[j] = formatter(&m.tasks[i])
			}
		}
		allRows[i] = row
		if m.selectID > 0 && m.tasks[i].ID == m.selectID {
			selectIdx = i
		}
	}

	// Filter out columns where every row has an empty value
	keep := make([]bool, len(m.columns))
	for j := range m.columns {
		for _, row := range allRows {
			if row[j] != "" {
				keep[j] = true
				break
			}
		}
	}

	var filteredCols []string
	var filteredLabels []string
	for j := range m.columns {
		if keep[j] {
			filteredCols = append(filteredCols, m.columns[j])
			filteredLabels = append(filteredLabels, m.labels[j])
		}
	}
	m.columns = filteredCols
	m.labels = filteredLabels

	// Filter rows to match
	m.rowData = make([][]string, len(allRows))
	for i, row := range allRows {
		var filtered []string
		for j, cell := range row {
			if keep[j] {
				filtered = append(filtered, cell)
			}
		}
		m.rowData[i] = filtered
	}

	// Resolve per-row styles
	m.rowStyles = make([]taskwarrior.TaskStyle, len(m.tasks))
	for i := range m.tasks {
		m.rowStyles[i] = resolveTaskStyle(&m.tasks[i], m.cfg)
	}

	// Set cursor
	m.cur.total = len(m.rowData)
	m.cur.cursor = selectIdx
	m.cur.clamp()
	m.selectID = 0
}

func (m tasksModel) View() string {
	if len(m.rowData) == 0 {
		return "No tasks."
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
			return m.rowStyles[row].ToLipgloss()
		})

	rendered := m.cur.underlineRow(t.Render())
	return lipgloss.NewStyle().PaddingLeft(1).Render(rendered)
}

func (m *tasksModel) SetSize(width, height int) {
	m.width = width
	m.height = height
	m.cur.height = height
}

// SelectedTask returns the currently selected task, or nil.
func (m *tasksModel) SelectedTask() *taskwarrior.Task {
	if m.cur.cursor < 0 || m.cur.cursor >= len(m.tasks) {
		return nil
	}
	return &m.tasks[m.cur.cursor]
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
