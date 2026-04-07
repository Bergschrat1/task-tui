package tui

import (
	"fmt"

	"task-tui-go/internal/taskwarrior"

	"charm.land/bubbles/v2/help"
	"charm.land/bubbles/v2/key"
	tea "charm.land/bubbletea/v2"
	"charm.land/lipgloss/v2"
)

type activeTab int

const (
	tabTasks activeTab = iota
	tabProjects
	tabContexts
	tabCount
)

var tabNames = [tabCount]string{"Tasks", "Projects", "Contexts"}

type Model struct {
	cli    *taskwarrior.TaskCli
	config *taskwarrior.Config
	report string
	help   help.Model

	activeTab activeTab
	tasks     tasksModel
	projects  projectsModel
	contexts  contextsModel

	// Dialog state
	dialog        dialogKind
	confirmDialog confirmModel
	inputDialog   textInputModel
	pending       pendingAction
	pendingTask   *taskwarrior.Task

	width  int
	height int
}

func NewModel(cli *taskwarrior.TaskCli, report string) Model {
	cfg := cli.GetConfig()
	return Model{
		cli:       cli,
		config:    cfg,
		report:    report,
		help:      help.New(),
		activeTab: tabTasks,
		tasks:     newTasksModel(cli, cfg, report),
		projects:  newProjectsModel(cli),
		contexts:  newContextsModel(cli),
	}
}

func (m Model) Init() tea.Cmd {
	return tea.Batch(
		m.tasks.refreshCmd(),
		m.projects.refreshCmd(),
		m.contexts.refreshCmd(),
	)
}

func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width = msg.Width
		m.height = msg.Height
		contentHeight := msg.Height - 3 // tab bar + footer
		m.tasks.SetSize(msg.Width, contentHeight)
		m.projects.SetSize(msg.Width, contentHeight)
		m.contexts.SetSize(msg.Width, contentHeight)
		return m, nil

	case editFinishedMsg:
		// Returned from $EDITOR
		return m, tea.Batch(
			m.tasks.refreshCmd(),
			m.projects.refreshCmd(),
		)

	case taskActionDoneMsg:
		return m, tea.Batch(
			m.tasks.refreshCmd(),
			m.projects.refreshCmd(),
		)

	case taskAddedMsg:
		m.tasks.selectID = msg.id
		return m, tea.Batch(
			m.tasks.refreshCmd(),
			m.projects.refreshCmd(),
		)

	case taskModifiedMsg:
		m.tasks.selectID = msg.id
		return m, tea.Batch(
			m.tasks.refreshCmd(),
			m.projects.refreshCmd(),
		)

	case contextSwitchedMsg:
		return m, tea.Batch(
			m.tasks.refreshCmd(),
			m.contexts.refreshCmd(),
		)

	case projectRefreshMsg:
		m.projects, _ = m.projects.Update(msg)
		return m, nil

	case contextRefreshMsg:
		m.contexts, _ = m.contexts.Update(msg)
		return m, nil
	}

	// Route to dialog if active
	if m.dialog != dialogNone {
		return m.updateDialog(msg)
	}

	// Handle global keys
	if msg, ok := msg.(tea.KeyPressMsg); ok {
		switch {
		case key.Matches(msg, keys.Quit):
			return m, tea.Quit

		case key.Matches(msg, keys.PrevTab):
			m.activeTab = (m.activeTab + tabCount - 1) % tabCount
			return m, nil

		case key.Matches(msg, keys.NextTab):
			m.activeTab = (m.activeTab + 1) % tabCount
			return m, nil

		case key.Matches(msg, keys.Help):
			m.help.ShowAll = !m.help.ShowAll
		}

		// Tab-specific key handling
		switch m.activeTab {
		case tabTasks:
			return m.updateTasksTab(msg)
		case tabContexts:
			return m.updateContextsTab(msg)
		}
	}

	// Pass non-key messages to active tab
	return m.updateActiveTab(msg)
}

func (m Model) updateActiveTab(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmd tea.Cmd
	switch m.activeTab {
	case tabTasks:
		m.tasks, cmd = m.tasks.Update(msg)
	case tabProjects:
		m.projects, cmd = m.projects.Update(msg)
	case tabContexts:
		m.contexts, cmd = m.contexts.Update(msg)
	}
	return m, cmd
}

func (m Model) updateTasksTab(msg tea.KeyPressMsg) (tea.Model, tea.Cmd) {
	switch {
	case key.Matches(msg, keys.Refresh):
		return m, m.tasks.refreshCmd()

	case key.Matches(msg, keys.Add):
		m.dialog = dialogTextInput
		m.inputDialog = newTextInputModel("Enter task description:")
		m.pending = actionAdd
		return m, m.inputDialog.textInput.Focus()

	case key.Matches(msg, keys.Done):
		task := m.tasks.SelectedTask()
		if task == nil {
			return m, nil
		}
		m.dialog = dialogConfirm
		m.confirmDialog = newConfirmModel(fmt.Sprintf("Mark task %d done?\n%s", task.ID, task.Description))
		m.pending = actionDone
		m.pendingTask = task
		return m, nil

	case key.Matches(msg, keys.Delete):
		task := m.tasks.SelectedTask()
		if task == nil {
			return m, nil
		}
		m.dialog = dialogConfirm
		m.confirmDialog = newConfirmModel(fmt.Sprintf("Delete task %d?\n%s", task.ID, task.Description))
		m.pending = actionDelete
		m.pendingTask = task
		return m, nil

	case key.Matches(msg, keys.Modify):
		task := m.tasks.SelectedTask()
		if task == nil {
			return m, nil
		}
		m.dialog = dialogTextInput
		m.inputDialog = newTextInputModel(fmt.Sprintf("Modify task %d:", task.ID))
		m.pending = actionModify
		m.pendingTask = task
		return m, m.inputDialog.textInput.Focus()

	case key.Matches(msg, keys.Annotate):
		task := m.tasks.SelectedTask()
		if task == nil {
			return m, nil
		}
		m.dialog = dialogTextInput
		m.inputDialog = newTextInputModel(fmt.Sprintf("Annotate task %d:", task.ID))
		m.pending = actionAnnotate
		m.pendingTask = task
		return m, m.inputDialog.textInput.Focus()

	case key.Matches(msg, keys.Log):
		m.dialog = dialogTextInput
		m.inputDialog = newTextInputModel("Log completed task:")
		m.pending = actionLog
		return m, m.inputDialog.textInput.Focus()

	case key.Matches(msg, keys.StartStop):
		task := m.tasks.SelectedTask()
		if task == nil {
			return m, nil
		}
		return m, m.toggleStartStop(task)

	case key.Matches(msg, keys.Edit):
		task := m.tasks.SelectedTask()
		if task == nil {
			return m, nil
		}
		m.tasks.selectID = task.ID
		cmd := tea.ExecProcess(m.cli.EditTaskCmd(task), func(err error) tea.Msg {
			return editFinishedMsg{err: err}
		})
		return m, cmd
	}

	// Pass remaining keys to table navigation
	var cmd tea.Cmd
	m.tasks, cmd = m.tasks.Update(msg)
	return m, cmd
}

type editFinishedMsg struct {
	err error
}

func (m Model) updateContextsTab(msg tea.KeyPressMsg) (tea.Model, tea.Cmd) {
	switch {
	case key.Matches(msg, keys.Enter):
		ctx := m.contexts.SelectedContext()
		if ctx == nil {
			return m, nil
		}
		return m, m.switchContext(ctx)
	}

	var cmd tea.Cmd
	m.contexts, cmd = m.contexts.Update(msg)
	return m, cmd
}

func (m Model) switchContext(ctx *taskwarrior.ContextInfo) tea.Cmd {
	return func() tea.Msg {
		name := ctx.Name
		_ = m.cli.SetContext(name)
		// Return a refresh message to reload everything
		return contextSwitchedMsg{}
	}
}

type contextSwitchedMsg struct{}

func (m Model) updateDialog(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch m.dialog {
	case dialogConfirm:
		var cmd tea.Cmd
		var result *bool
		m.confirmDialog, cmd, result = m.confirmDialog.Update(msg)
		if result != nil {
			m.dialog = dialogNone
			if *result {
				return m, m.executeAction()
			}
			m.pending = actionNone
			m.pendingTask = nil
		}
		return m, cmd

	case dialogTextInput:
		var cmd tea.Cmd
		var result *string
		m.inputDialog, cmd, result = m.inputDialog.Update(msg)
		if result != nil {
			m.dialog = dialogNone
			if *result != "" {
				return m, m.executeTextAction(*result)
			}
			m.pending = actionNone
			m.pendingTask = nil
		}
		return m, cmd
	}

	return m, nil
}

func (m *Model) executeAction() tea.Cmd {
	task := m.pendingTask
	action := m.pending
	m.pending = actionNone
	m.pendingTask = nil

	switch action {
	case actionDone:
		return func() tea.Msg {
			_ = m.cli.SetTaskDone(task)
			return taskActionDoneMsg{}
		}
	case actionDelete:
		return func() tea.Msg {
			_ = m.cli.DeleteTask(task)
			return taskActionDoneMsg{}
		}
	}
	return nil
}

func (m *Model) executeTextAction(value string) tea.Cmd {
	task := m.pendingTask
	action := m.pending
	m.pending = actionNone
	m.pendingTask = nil

	switch action {
	case actionAdd:
		return func() tea.Msg {
			id, err := m.cli.AddTask(value)
			if err != nil {
				return taskActionDoneMsg{}
			}
			return taskAddedMsg{id: id}
		}
	case actionModify:
		return func() tea.Msg {
			_ = m.cli.ModifyTask(task, value)
			return taskModifiedMsg{id: task.ID}
		}
	case actionAnnotate:
		return func() tea.Msg {
			_ = m.cli.AnnotateTask(task, value)
			return taskModifiedMsg{id: task.ID}
		}
	case actionLog:
		return func() tea.Msg {
			_ = m.cli.LogTask(value)
			return taskActionDoneMsg{}
		}
	}
	return nil
}

func (m *Model) toggleStartStop(task *taskwarrior.Task) tea.Cmd {
	return func() tea.Msg {
		if task.Start == nil {
			_ = m.cli.StartTask(task)
		} else {
			_ = m.cli.StopTask(task)
		}
		return taskModifiedMsg{id: task.ID}
	}
}

type taskActionDoneMsg struct{}
type taskAddedMsg struct{ id int }
type taskModifiedMsg struct{ id int }

func (m Model) View() tea.View {
	if m.width == 0 {
		v := tea.NewView("Loading...")
		v.AltScreen = true
		return v
	}

	// Tab bar
	tabBar := m.renderTabBar()

	// Content
	var content string
	switch m.activeTab {
	case tabTasks:
		content = m.tasks.View()
	case tabProjects:
		content = m.projects.View()
	case tabContexts:
		content = m.contexts.View()
	}

	// Footer
	footer := m.getHelpView()

	view := lipgloss.JoinVertical(lipgloss.Left, tabBar, content, footer)

	// Overlay dialog if active
	if m.dialog != dialogNone {
		switch m.dialog {
		case dialogConfirm:
			view = m.confirmDialog.View(m.width, m.height)
		case dialogTextInput:
			view = m.inputDialog.View(m.width, m.height)
		}
	}

	v := tea.NewView(view)
	v.AltScreen = true
	return v
}

func (m Model) renderTabBar() string {
	var tabs []string
	for i := 0; i < int(tabCount); i++ {
		style := lipgloss.NewStyle().Padding(0, 2)
		if activeTab(i) == m.activeTab {
			style = style.Bold(true).
				Foreground(lipgloss.Color("229")).
				Background(lipgloss.Color("57"))
		} else {
			style = style.Foreground(lipgloss.Color("250"))
		}
		tabs = append(tabs, style.Render(tabNames[i]))
	}

	tabRow := lipgloss.JoinHorizontal(lipgloss.Top, tabs...)
	return lipgloss.NewStyle().
		BorderStyle(lipgloss.NormalBorder()).
		BorderBottom(true).
		BorderForeground(lipgloss.Color("240")).
		Width(m.width).
		Render(tabRow)
}

func (m Model) getHelpView() string {
	var km help.KeyMap
	switch m.activeTab {
	case tabTasks:
		km = tasksKeyMap{}
	case tabProjects:
		km = projectsKeyMap{}
	case tabContexts:
		km = contextsKeyMap{}
	}

	return lipgloss.NewStyle().
		Width(m.width).
		Render(m.help.View(km))
}
