package tui

import (
	"task-tui/internal/taskwarrior"

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
	help help.Model

	activeTab activeTab
	tasks     tasksModel
	projects  projectsModel
	contexts  contextsModel

	width  int
	height int
}

func NewModel(cli *taskwarrior.TaskCli, report string) Model {
	cfg := cli.GetConfig()
	return Model{
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

	// Handle global keys (but not when a dialog is active)
	if msg, ok := msg.(tea.KeyPressMsg); ok && m.tasks.dialog == dialogNone {
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
	}

	// Route to active tab
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

	// Add a padding so that the footer is always at the bottom
	tabBarHeight := lipgloss.Height(tabBar)
	contentHeight := lipgloss.Height(content)
	footerHeight := lipgloss.Height(footer)
	gap := max(m.height-tabBarHeight-contentHeight-footerHeight, 0)
	spacer := lipgloss.NewStyle().Height(gap).Render("")

	view := lipgloss.JoinVertical(lipgloss.Left, tabBar, content, spacer, footer)
	baseLayer := lipgloss.NewLayer(view)
	compositor := lipgloss.NewCompositor(baseLayer)

	// Overlay dialog if active
	if m.tasks.dialog != dialogNone {
		var dialogView string
		switch m.tasks.dialog {
		case dialogConfirm:
			dialogView = m.tasks.confirmDialog.View()
		case dialogTextInput:
			dialogView = m.tasks.inputDialog.View()
		}
		popupLayer := lipgloss.NewLayer(dialogView)
		compositor.AddLayers(popupLayer.X(m.width/2 - popupLayer.Width()/2).Y(m.height/2 - popupLayer.Height()/2))
	}

	v := tea.NewView(compositor.Render())
	v.AltScreen = true
	return v
}

func (m Model) renderTabBar() string {
	var tabs []string
	for i := range int(tabCount) {
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
