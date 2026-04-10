# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

task-tui is a terminal user interface (TUI) for Taskwarrior built with Go and Bubble Tea. It uses v2 of all the libraries from the Charm project.

## Development Commands

```bash
nix develop          # Enter nix shell (provides go, gotools, gopls, golangci-lint)
go build ./...       # Build
go run .             # Launch the TUI (default report: next)
go run . --report next --verbose  # Launch with debug logging
go test ./...        # Run tests
golangci-lint run    # Lint
```

## Architecture

### Package Structure

- **main.go**: Entry point. Parses `--report` and `--verbose` flags, sets up file logging, creates TaskCli and TUI model, runs Bubble Tea program.
- **internal/taskwarrior/**: Taskwarrior domain layer (not importable outside this module)
  - `cli.go`: `TaskCli` wraps Taskwarrior CLI via subprocess. Handles task export, context management, and all task mutations.
  - `models.go`: `Task` struct with JSON deserialization, `ContextInfo`, `Status`/`VirtualTag` enums.
  - `config.go`: Parses `task show` output into `Config` (due days, color precedence, color rules).
  - `color.go`: `TaskStyle` (fg/bg/bold/underline), color config parsing (named colors, colorN, rgbRGB, grayN).
- **internal/tui/**: Bubble Tea UI layer
  - `app.go`: Root `Model` with tab management, dialog state, message routing. Implements Elm architecture (Init/Update/View).
  - `tasks.go`: Tasks tab using lipgloss/v2/table renderer with per-row color styling and manual cursor/scroll.
  - `projects.go`: Projects tab with task count aggregation per project.
  - `contexts.go`: Contexts tab with context switching.
  - `dialog.go`: Confirm and text input dialog models.
  - `keys.go`: Key bindings (`keyMap` struct) and per-tab `help.KeyMap` implementations.
  - `style.go`: Resolves task virtual tags to composite `TaskStyle` via color precedence rules.
- **internal/util/**: Shared utilities
  - `vague.go`: Human-friendly date formatting ("2h ago", "3d", "1w").

### Data Flow

1. `TaskCli.ExportTasks()` runs `task export <report>` with context filters
2. JSON output unmarshaled into `[]Task`
3. `computeVirtualTags()` assigns virtual tags (OVERDUE, BLOCKED, ACTIVE, etc.)
4. `resolveTaskStyle()` maps virtual tags to color styles via Taskwarrior's `rule.precedence.color`
5. `tasksModel.View()` renders via lipgloss table with `StyleFunc` for per-row coloring

### Key Patterns

- Elm architecture: `Model.Update(msg) -> (Model, Cmd)` with async commands returning messages
- Task actions return `tea.Cmd` closures that invoke TaskCli, then return refresh messages
- Dialog state managed via `dialogKind` enum + `pendingAction` + `pendingTask` on root model
- Tab-specific messages (e.g., `taskRefreshMsg`) routed in root `Update()` before tab dispatch

## Debugging

Runtime logs written to `task-tui.log`. Use `--verbose` for debug-level output. Check this file first for UI issues.
