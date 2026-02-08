from datetime import datetime
from types import SimpleNamespace
from typing import cast
from uuid import uuid4

import pytest

from task_tui.data_models import ContextInfo, Status, Task
from task_tui.task_cli import TaskCli


def _make_task(start: datetime | None = None) -> Task:
    now = datetime(2024, 1, 1, 0, 0, 0)
    return Task(
        id=1,
        description="task",
        entry=cast(datetime, now.isoformat()),
        modified=cast(datetime, now.isoformat()),
        due=None,
        start=cast(datetime, start.isoformat()) if start else None,
        scheduled=None,
        wait=None,
        end=None,
        until=None,
        recur=None,
        project=None,
        status=Status.PENDING,
        uuid=uuid4(),
        urgency=0.0,
        annotations=[],
        priority=None,
        tags=set(),
        depends=set(),
        virtual_tags=set(),
    )


@pytest.fixture()
def cli_with_spy(monkeypatch: pytest.MonkeyPatch) -> tuple[TaskCli, list[tuple[str, ...]]]:
    calls: list[tuple[str, ...]] = []

    def fake_run(self: TaskCli, *args: str) -> SimpleNamespace:
        calls.append(args)
        return SimpleNamespace(stdout="", returncode=0)

    monkeypatch.setattr(TaskCli, "_run_task", fake_run, raising=False)
    return TaskCli(), calls


def test_start_task_uses_task_cli(cli_with_spy: tuple[TaskCli, list[tuple[str, ...]]]) -> None:
    cli, calls = cli_with_spy
    task = _make_task()
    calls.clear()

    cli.start_task(task)

    assert calls == [(str(task.uuid), "start")]


def test_stop_task_uses_task_cli(cli_with_spy: tuple[TaskCli, list[tuple[str, ...]]]) -> None:
    cli, calls = cli_with_spy
    task = _make_task(start=datetime(2024, 1, 1, 12, 0, 0))
    calls.clear()

    cli.stop_task(task)

    assert calls == [(str(task.uuid), "stop")]


def test_modify_task_uses_task_cli(cli_with_spy: tuple[TaskCli, list[tuple[str, ...]]]) -> None:
    cli, calls = cli_with_spy
    task = _make_task()
    calls.clear()

    cli.modify_task(task, "project:Home +tag")

    assert calls == [(str(task.uuid), "modify", "project:Home", "+tag")]


def test_log_task_uses_task_cli(cli_with_spy: tuple[TaskCli, list[tuple[str, ...]]]) -> None:
    cli, calls = cli_with_spy

    cli.log_task("read book")

    assert calls[0] == ("show",)
    assert calls[1] == ("log", "read", "book")


def test_annotate_task_uses_task_cli(cli_with_spy: tuple[TaskCli, list[tuple[str, ...]]]) -> None:
    cli, calls = cli_with_spy
    task = _make_task()

    cli.annotate_task(task, "note")

    assert calls[0] == ("show",)
    assert calls[1] == (str(task.uuid), "annotate", "note")


def test_delete_task_uses_task_cli(cli_with_spy: tuple[TaskCli, list[tuple[str, ...]]]) -> None:
    cli, calls = cli_with_spy
    task = _make_task()

    cli.delete_task(task)

    assert calls[0] == ("show",)
    assert calls[1] == ("rc.confirmation=off", "rc.recurrence.confirmation=no", str(task.id), "delete")


def test_get_context_reads_filter(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(self: TaskCli, *args: str) -> SimpleNamespace:
        if args == ("show",):
            return SimpleNamespace(stdout="", returncode=0)
        if args == ("_get", "rc.context"):
            return SimpleNamespace(stdout="work\n", returncode=0)
        if args == ("_get", "rc.context.work.read"):
            return SimpleNamespace(stdout="project:Work\n", returncode=0)
        if args == ("_get", "rc.context.work"):
            return SimpleNamespace(stdout="", returncode=0)
        return SimpleNamespace(stdout="", returncode=0)

    monkeypatch.setattr(TaskCli, "_run_task", fake_run, raising=False)
    cli = TaskCli()

    context = cli.get_context()

    assert context == ContextInfo(name="work", read_filter="project:Work", is_active=True)


def test_export_tasks_applies_context_filter(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, ...]] = []
    task_json = (
        '{"id":1,"description":"task","entry":"2024-01-01T00:00:00","modified":"2024-01-01T00:00:00",'
        '"status":"pending","uuid":"00000000-0000-0000-0000-000000000001","urgency":0.0,'
        '"tags":[],"depends":[],"annotations":[]}'
    )

    def fake_run(self: TaskCli, *args: str) -> SimpleNamespace:
        calls.append(args)
        if args == ("show",):
            return SimpleNamespace(stdout="", returncode=0)
        if args == ("_get", "rc.context"):
            return SimpleNamespace(stdout="work\n", returncode=0)
        if args == ("_get", "rc.context.work.read"):
            return SimpleNamespace(stdout="project:Work +next\n", returncode=0)
        if args == ("_get", "rc.context.work"):
            return SimpleNamespace(stdout="", returncode=0)
        if "export" in args:
            return SimpleNamespace(stdout=task_json, returncode=0)
        return SimpleNamespace(stdout="", returncode=0)

    monkeypatch.setattr(TaskCli, "_run_task", fake_run, raising=False)
    cli = TaskCli()

    tasks = cli.export_tasks("next")

    export_calls = [call for call in calls if "export" in call]
    assert export_calls == [("rc.json.array=0", "rc.defaultheight=0", "project:Work", "+next", "export", "next")]
    assert len(tasks) == 1
