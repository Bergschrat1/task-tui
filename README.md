# task-tui

A terminal user interface for [Taskwarrior](https://taskwarrior.org/) built with Go and [Bubble Tea](https://github.com/charmbracelet/bubbletea).

## Features

- View tasks using any Taskwarrior report (default: `next`)
- Per-row color styling matching Taskwarrior's color rules and precedence
- Add, complete, delete, modify, annotate, start/stop, log, and edit tasks
- Project summary with pending/completed counts and urgency
- Context switching
- Vim-style navigation (j/k, ctrl+u/d, g/G)
- Open tasks in `$EDITOR` via `task edit`

## Installation

Requires Go 1.22+ and [Taskwarrior 3](https://taskwarrior.org/).

```bash
go install github.com/jokehboy/task-tui@latest
```

Or build from source:

```bash
git clone https://github.com/jokehboy/task-tui.git
cd task-tui
go build .
```

## Usage

```bash
./task-tui                    # default report: next
./task-tui --report ready     # use a different report
./task-tui --verbose          # enable debug logging to task-tui.log
```

## Keybindings

| Key       | Action       |
|-----------|--------------|
| j/k       | Navigate     |
| ctrl+u/d  | Page up/down |
| g/G       | Top/bottom   |
| a         | Add task     |
| d         | Mark done    |
| del       | Delete task  |
| m         | Modify task  |
| A         | Annotate     |
| s         | Start/stop   |
| l         | Log task     |
| e         | Edit in $EDITOR |
| r         | Refresh      |
| [/]       | Switch tabs  |
| enter     | Select (contexts tab) |
| ?         | Toggle help  |
| q/esc     | Quit         |

## Roadmap

Features from the Python version not yet ported to Go:

- [ ] **Task review workflow** — step-through dialog for reviewing tasks that haven't been reviewed recently, with actions to mark reviewed, skip, edit, modify, complete, or delete. Includes automatic setup of the `reviewed` UDA.
- [ ] **User notifications** — toast/status messages for action confirmations ("Task modified", "Context set to work") and error feedback shown in the UI rather than only logged to file.
- [ ] **Zebra striping** — alternating row background colors in tables for better readability.
