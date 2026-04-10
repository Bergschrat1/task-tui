package main

import (
	"flag"
	"fmt"
	"os"

	"task-tui/internal/taskwarrior"
	"task-tui/internal/tui"

	tea "charm.land/bubbletea/v2"
	"charm.land/log/v2"
)

func main() {
	report := flag.String("report", "next", "Taskwarrior report to display")
	verbose := flag.Bool("verbose", false, "Enable debug logging")
	flag.Parse()

	// Set up file-based logging
	logFile, err := os.OpenFile("task-tui.log", os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0o644)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Warning: could not open log file: %v\n", err)
	} else {
		defer logFile.Close()
		log.SetOutput(logFile)
	}

	if *verbose {
		log.SetLevel(log.DebugLevel)
	} else {
		log.SetLevel(log.InfoLevel)
	}

	log.Info("starting task-tui", "report", *report)

	cli, err := taskwarrior.NewTaskCli()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}

	model := tui.NewModel(cli, *report)
	p := tea.NewProgram(model)

	if _, err := p.Run(); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
}
