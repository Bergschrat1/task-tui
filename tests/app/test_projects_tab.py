import asyncio
import importlib
import sys
from datetime import datetime
from uuid import UUID

import pytest
from textual.widgets import TabbedContent

import task_tui.task_cli as task_cli_mod
from task_tui.config import Config
from task_tui.data_models import Status, Task
from task_tui.widgets import ProjectSummary


def make_task(
    *,
    task_id: int,
    description: str,
    project: str | None,
    status: Status,
    urgency: float,
    reference_uuid: str,
    timestamp: datetime,
) -> Task:
    return Task(
        id=task_id,
        description=description,
        entry=timestamp.isoformat(),
        modified=timestamp.isoformat(),
        due=None,
        start=None,
        scheduled=None,
        wait=None,
        end=None,
        until=None,
        recur=None,
        project=project,
        status=status,
        uuid=UUID(reference_uuid),
        urgency=urgency,
        annotations=[],
        priority=None,
        tags=set(),
        depends=set(),
        virtual_tags=set(),
    )


def test_projects_tab_updates_with_tasks(monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyTaskCli:
        def __init__(self) -> None:
            pass

    monkeypatch.setattr(task_cli_mod, "TaskCli", DummyTaskCli)
    if "task_tui.app" in sys.modules:
        del sys.modules["task_tui.app"]
    app_module = importlib.import_module("task_tui.app")

    timestamp = datetime(2024, 5, 1, 12, 0, 0)
    tasks = [
        make_task(
            task_id=1,
            description="Write docs",
            project="alpha",
            status=Status.PENDING,
            urgency=3.5,
            reference_uuid="00000000-0000-0000-0000-000000000001",
            timestamp=timestamp,
        ),
        make_task(
            task_id=2,
            description="Ship release",
            project="alpha",
            status=Status.COMPLETED,
            urgency=1.0,
            reference_uuid="00000000-0000-0000-0000-000000000002",
            timestamp=timestamp,
        ),
        make_task(
            task_id=3,
            description="Triage inbox",
            project=None,
            status=Status.PENDING,
            urgency=2.0,
            reference_uuid="00000000-0000-0000-0000-000000000003",
            timestamp=timestamp,
        ),
    ]

    monkeypatch.setattr(app_module.task_cli, "get_config", lambda: Config(""), raising=False)
    monkeypatch.setattr(app_module.task_cli, "export_tasks", lambda report: tasks, raising=False)
    monkeypatch.setattr(
        app_module.task_cli,
        "get_report_columns",
        lambda report: [("id", "ID"), ("description", "Description")],
        raising=False,
    )

    app = app_module.TaskTuiApp("next")

    async def run_app() -> list[list[object]]:
        async with app.run_test() as pilot:
            await pilot.pause()

            tabbed_content = app.query_one(TabbedContent)
            assert tabbed_content.active == "tasks"

            project_summary = app.query_one(ProjectSummary)
            return [project_summary.get_row_at(index) for index in range(project_summary.row_count)]

    rows = asyncio.run(run_app())

    assert rows == [
        ["(none)", 1, 1, 0, "2.00"],
        ["alpha", 2, 1, 1, "4.50"],
    ]


def test_tab_navigation_shortcuts(monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyTaskCli:
        def __init__(self) -> None:
            pass

    monkeypatch.setattr(task_cli_mod, "TaskCli", DummyTaskCli)
    if "task_tui.app" in sys.modules:
        del sys.modules["task_tui.app"]
    app_module = importlib.import_module("task_tui.app")

    monkeypatch.setattr(app_module.task_cli, "get_config", lambda: Config(""), raising=False)
    monkeypatch.setattr(app_module.task_cli, "export_tasks", lambda report: [], raising=False)
    monkeypatch.setattr(
        app_module.task_cli, "get_report_columns", lambda report: [("id", "ID"), ("description", "Description")], raising=False
    )

    app = app_module.TaskTuiApp("next")

    async def run_app() -> None:
        async with app.run_test() as pilot:
            await pilot.pause()

            tabbed_content = app.query_one(TabbedContent)
            assert tabbed_content.active == "tasks"

            await pilot.press("]")
            await pilot.pause()
            assert tabbed_content.active == "projects"

            await pilot.press("[")
            await pilot.pause()
            assert tabbed_content.active == "tasks"

    asyncio.run(run_app())
