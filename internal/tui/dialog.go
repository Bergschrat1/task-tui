package tui

import (
	"charm.land/bubbles/v2/key"
	"charm.land/bubbles/v2/textinput"
	tea "charm.land/bubbletea/v2"
	"charm.land/lipgloss/v2"
)

// Dialog types
type dialogKind int

const (
	dialogNone dialogKind = iota
	dialogConfirm
	dialogTextInput
)

// Pending action that triggered the dialog
type pendingAction int

const (
	actionNone pendingAction = iota
	actionAdd
	actionDone
	actionDelete
	actionModify
	actionAnnotate
	actionLog
)

// confirmModel handles yes/no confirmations.
type confirmModel struct {
	prompt string
}

func newConfirmModel(prompt string) confirmModel {
	return confirmModel{prompt: prompt}
}

func (m confirmModel) Update(msg tea.Msg) (confirmModel, tea.Cmd, *bool) {
	if msg, ok := msg.(tea.KeyPressMsg); ok {
		switch {
		case key.Matches(msg, key.NewBinding(key.WithKeys("y", "enter"))):
			result := true
			return m, nil, &result
		case key.Matches(msg, key.NewBinding(key.WithKeys("n", "esc", "escape"))):
			result := false
			return m, nil, &result
		}
	}
	return m, nil, nil
}

func (m confirmModel) View() string {
	boxStyle := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(lipgloss.Color("62")).
		Padding(1, 2).
		Width(50).
		Align(lipgloss.Center)

	content := lipgloss.JoinVertical(lipgloss.Center,
		m.prompt,
		"",
		lipgloss.NewStyle().Foreground(lipgloss.Color("241")).Render("[y]es / [n]o"),
	)

	return boxStyle.Render(content)
}

// textInputModel handles single-line text input.
type textInputModel struct {
	prompt    string
	textInput textinput.Model
}

func newTextInputModel(prompt string) textInputModel {
	ti := textinput.New()
	ti.Placeholder = "..."
	ti.Focus()
	ti.CharLimit = 256
	ti.SetWidth(44)

	return textInputModel{
		prompt:    prompt,
		textInput: ti,
	}
}

func (m textInputModel) Update(msg tea.Msg) (textInputModel, tea.Cmd, *string) {
	if msg, ok := msg.(tea.KeyPressMsg); ok {
		switch msg.String() {
		case "enter":
			value := m.textInput.Value()
			return m, nil, &value
		case "esc", "escape":
			empty := ""
			return m, nil, &empty
		}
	}

	var cmd tea.Cmd
	m.textInput, cmd = m.textInput.Update(msg)
	return m, cmd, nil
}

func (m textInputModel) View() string {
	boxStyle := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(lipgloss.Color("62")).
		Width(50).
		Align(lipgloss.Center)

	content := lipgloss.JoinVertical(lipgloss.Center,
		m.prompt,
		"",
		m.textInput.View(),
		"",
		lipgloss.NewStyle().Foreground(lipgloss.Color("241")).Render("[enter] submit / [esc] cancel"),
	)

	return boxStyle.Render(content)
}
