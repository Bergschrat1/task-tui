# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

task-tui is a terminal user interface (TUI) for Taskwarrior built with Python 3.13+, Textual, and Typer.

## Development Commands

```bash
nix develop              # Enter nix shell for development
uv run task_tui          # Launch the TUI (or just `task-tui` if installed)
uv run task_tui health   # Smoke check that CLI bootstraps correctly
uv run ruff check src tests  # Lint
uv run ruff format       # Format
uv run ty check          # Type check
uv run pytest            # Run tests
uv run pytest -k <pattern>  # Run specific tests
just                     # Run format, lint, typecheck, and test
```

## Architecture

### Module Structure (`src/task_tui/`)

- **main.py**: Typer CLI entry point. Defines `health` and `task_tui` commands. Default invocation runs the TUI.
- **app.py**: Core Textual application (`TaskTuiApp`). Contains:
  - `TaskStore`: In-memory task collection with virtual tag computation and column accessors
  - Tab management (Tasks, Projects, Contexts)
  - All task actions (add, done, delete, modify, annotate, start/stop, log)
- **task_cli.py**: `TaskCli` class wraps Taskwarrior CLI commands via subprocess. Handles task export, context management, and all task mutations.
- **widgets.py**: Custom Textual widgets:
  - `RowMarkerTable`: DataTable variant showing `▶` row indicator instead of cell highlights
  - `TaskReport`: Main task table with vim-style keybindings (j/k navigation)
  - `ProjectSummary`/`ContextSummary`: Aggregation tables
  - `ConfirmDialog`/`TextInput`: Modal screens for user input
- **data_models.py**: Pydantic models for `Task`, `ContextInfo`, and enums (`Status`, `VirtualTag`)
- **config.py**: Parses Taskwarrior's `task show` output into color styles and settings

### Data Flow

1. `TaskCli.export_tasks()` runs `task export <report>` with context filters
2. JSON output parsed into `Task` Pydantic models
3. `TaskStore` wraps tasks, computes virtual tags (OVERDUE, BLOCKED, ACTIVE, etc.)
4. `TaskTuiApp._update_table()` reads columns from report config and renders via `TaskReport`

### Key Patterns

- Task actions post `TasksChanged` message to trigger table refresh
- Virtual tags derive from task state (due dates, dependencies, status) per `TaskStore._update_virtual_tags()`
- Color precedence from Taskwarrior config determines row styling

## Coding Standards

- Type hints required on all public callables; avoid `typing.Any`
- 150-character line limit enforced by ruff
- Google-style docstrings (ruff ANN/D rules)
- Tests in `tests/` using pytest; fixtures in `test_data/`

## Debugging

Runtime logs written to `task-tui.log`. Check this file first for UI issues.
