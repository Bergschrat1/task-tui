package tui

import "charm.land/bubbles/v2/key"

type keyMap struct {
	Quit      key.Binding
	PrevTab   key.Binding
	NextTab   key.Binding
	Up        key.Binding
	Down      key.Binding
	PageUp    key.Binding
	PageDown  key.Binding
	GoTop     key.Binding
	GoBottom  key.Binding
	Add       key.Binding
	Done      key.Binding
	Delete    key.Binding
	Modify    key.Binding
	Annotate  key.Binding
	StartStop key.Binding
	Log       key.Binding
	Edit      key.Binding
	Refresh   key.Binding
	Enter     key.Binding
	Review    key.Binding
	Help      key.Binding
}

var keys = keyMap{
	Quit: key.NewBinding(
		key.WithKeys("q", "esc"),
		key.WithHelp("q", "quit"),
	),
	PrevTab: key.NewBinding(
		key.WithKeys("["),
		key.WithHelp("[", "prev tab"),
	),
	NextTab: key.NewBinding(
		key.WithKeys("]"),
		key.WithHelp("]", "next tab"),
	),
	Up: key.NewBinding(
		key.WithKeys("k", "up"),
		key.WithHelp("↑/k", "up"),
	),
	Down: key.NewBinding(
		key.WithKeys("j", "down"),
		key.WithHelp("↓/j", "down"),
	),
	PageUp: key.NewBinding(
		key.WithKeys("ctrl+u"),
		key.WithHelp("ctrl+u", "page up"),
	),
	PageDown: key.NewBinding(
		key.WithKeys("ctrl+d"),
		key.WithHelp("ctrl+d", "page down"),
	),
	GoTop: key.NewBinding(
		key.WithKeys("g"),
		key.WithHelp("g", "top"),
	),
	GoBottom: key.NewBinding(
		key.WithKeys("G"),
		key.WithHelp("G", "bottom"),
	),
	Add: key.NewBinding(
		key.WithKeys("a"),
		key.WithHelp("a", "add"),
	),
	Done: key.NewBinding(
		key.WithKeys("d"),
		key.WithHelp("d", "done"),
	),
	Delete: key.NewBinding(
		key.WithKeys("delete", "backspace"),
		key.WithHelp("del", "delete"),
	),
	Modify: key.NewBinding(
		key.WithKeys("m"),
		key.WithHelp("m", "modify"),
	),
	Annotate: key.NewBinding(
		key.WithKeys("A"),
		key.WithHelp("A", "annotate"),
	),
	StartStop: key.NewBinding(
		key.WithKeys("s"),
		key.WithHelp("s", "start/stop"),
	),
	Log: key.NewBinding(
		key.WithKeys("l"),
		key.WithHelp("l", "log"),
	),
	Edit: key.NewBinding(
		key.WithKeys("e"),
		key.WithHelp("e", "edit"),
	),
	Refresh: key.NewBinding(
		key.WithKeys("r"),
		key.WithHelp("r", "refresh"),
	),
	Enter: key.NewBinding(
		key.WithKeys("enter"),
		key.WithHelp("enter", "select"),
	),
	Review: key.NewBinding(
		key.WithKeys("R"),
		key.WithHelp("R", "review"),
	),
	Help: key.NewBinding(
		key.WithKeys("?"),
		key.WithHelp("?", "toggle help"),
	),
}

