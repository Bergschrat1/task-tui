package main

import (
	"flag"
	"fmt"
	"os"

	"task-tui-go/internal/taskwarrior"
	"task-tui-go/internal/tui"

	tea "github.com/charmbracelet/bubbletea"
)

func main() {
	report := flag.String("report", "next", "Taskwarrior report to display")
	flag.Parse()

	cli, err := taskwarrior.NewTaskCli()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}

	model := tui.NewModel(cli, *report)
	p := tea.NewProgram(model, tea.WithAltScreen())

	if _, err := p.Run(); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
}
