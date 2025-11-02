# Repository Guidelines

## Project Structure & Module Organization
Core application code resides in `src/task_tui/`, with `app.py` wiring the Textual interface, `task_cli.py` providing the Taskwarrior bridge, and supporting modules (`config.py`, `data_models.py`, `widgets.py`, `utils.py`) handling configuration, schema validation, and reusable views. Entry points for Typer live in `main.py`. Tests are located in `tests/`, and fixtures that mirror a Taskwarrior workspace are under `test_data/`. Runtime logs land in `task-tui.log`; check this file first when debugging UI issues.

## Build, Test, and Development Commands
- `uv run task_tui`: launch the interactive TUI using the Typer entry point.
- `uv run python -m task_tui.main health`: quick smoke check that the CLI bootstraps correctly.
- `uv run ruff check src tests`: lint the codebase using the shared configuration in `pyproject.toml`.
- `uv run ruff format`: format the codebase using the shared configuration in `pyproject.toml`.
- `uv run pytest`: execute the test suite; add `-k <pattern>` for targeted runs.

## Coding Style & Naming Conventions
Follow standard Python 3.14 syntax with four-space indentation and type hints on public callables. Ruff enforces a 150-character line limit and the ANN/DOC rule sets, so prefer explicit annotations and concise docstrings describing intent rather than narration. Module names are snake_case; classes use CapWords, and user-facing Typer commands stay lowercase with hyphen-free verbs (see `main.py`).

## Testing Guidelines
Use `pytest` with test files named `test_*.py`; group related cases into classes when fixtures are shared. Mimic the patterns in `tests/test_config.py`, and pull structured data from `test_data/` instead of hard-coding paths so the suite remains hermetic. New features should include a regression test that exercises both the Typer CLI entry point and the Textual widget logic when feasible.

## Commit & Pull Request Guidelines
Commits should be small and purposeful; mimic the existing imperative, present-tense summaries such as “Handle task creation errors…”. When opening a pull request, include: 1) a brief problem statement, 2) the solution outline referencing key modules, 3) test evidence (`uv run pytest`) and any manual TUI checks, and 4) screenshots or terminal captures if the UI changes. Link related issues and call out configuration updates so reviewers can refresh local state.

## Configuration & Troubleshooting Notes
Local development expects Python managed by `uv`; keep dependencies in `pyproject.toml` and lock changes with `uv lock`. The sample Taskwarrior database in `test_data/` is safe for experimentation, but do not commit edits. If the TUI fails to start, run the health command and inspect `task-tui.log` before escalating.
