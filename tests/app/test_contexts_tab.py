import asyncio
import importlib
import sys
from datetime import datetime
from uuid import UUID

import pytest
from textual.widgets import TabbedContent

import task_tui.task_cli as task_cli_mod
from task_tui.config import Config
from task_tui.data_models import ContextInfo, Status, Task
from task_tui.widgets import ContextSummary


def make_task(task_id: int) -> Task:
    timestamp = datetime(2024, 5, 1, 12, 0, 0)
    return Task(
        id=task_id,
        description="Write docs",
        entry=timestamp.isoformat(),
        modified=timestamp.isoformat(),
        due=None,
        start=None,
        scheduled=None,
        wait=None,
        end=None,
        until=None,
        recur=None,
        project=None,
        status=Status.PENDING,
        uuid=UUID("00000000-0000-0000-0000-000000000001"),
        urgency=3.5,
        annotations=[],
        priority=None,
        tags=set(),
        depends=set(),
        virtual_tags=set(),
    )


def test_contexts_tab_updates_and_selects(monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyTaskCli:
        def __init__(self) -> None:
            pass

    monkeypatch.setattr(task_cli_mod, "TaskCli", DummyTaskCli)
    if "task_tui.app" in sys.modules:
        del sys.modules["task_tui.app"]
    app_module = importlib.import_module("task_tui.app")

    contexts = [
        ContextInfo(name="none", read_filter="", is_active=True),
        ContextInfo(name="work", read_filter="project:Work", is_active=False),
    ]
    set_context_calls: list[str] = []

    monkeypatch.setattr(app_module.task_cli, "get_config", lambda: Config(""), raising=False)
    monkeypatch.setattr(app_module.task_cli, "export_tasks", lambda report: [make_task(1)], raising=False)
    monkeypatch.setattr(
        app_module.task_cli,
        "get_report_columns",
        lambda report: [("id", "ID"), ("description", "Description")],
        raising=False,
    )
    monkeypatch.setattr(app_module.task_cli, "list_contexts", lambda: contexts, raising=False)
    monkeypatch.setattr(app_module.task_cli, "set_context", lambda name: set_context_calls.append(name), raising=False)

    app = app_module.TaskTuiApp("next")

    async def run_app() -> tuple[list[list[object]], list[str]]:
        async with app.run_test() as pilot:
            await pilot.press("]")
            await pilot.press("]")
            await pilot.pause()

            tabbed_content = app.query_one(TabbedContent)
            assert tabbed_content.active == "contexts"

            context_summary = app.query_one(ContextSummary)
            rows = [context_summary.get_row_at(index) for index in range(context_summary.row_count)]

            row_labels = []
            for index in range(context_summary.row_count):
                row_key = context_summary._row_locations.get_key(index)
                row = context_summary.rows.get(row_key) if row_key is not None else None
                row_labels.append(row.label.plain if row is not None and row.label is not None else "")

            await pilot.press("down")
            await pilot.pause()

            moved_row_labels = []
            for index in range(context_summary.row_count):
                row_key = context_summary._row_locations.get_key(index)
                row = context_summary.rows.get(row_key) if row_key is not None else None
                moved_row_labels.append(row.label.plain if row is not None and row.label is not None else "")

            await pilot.press("enter")
            await pilot.pause()

            return rows, moved_row_labels

    rows, row_labels = asyncio.run(run_app())

    assert rows == [
        ["none *", ""],
        ["work", "project:Work"],
    ]
    assert row_labels == [" ", "▶"]
    assert set_context_calls == ["work"]
