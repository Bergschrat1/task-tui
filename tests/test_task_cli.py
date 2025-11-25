from datetime import datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from task_tui.data_models import Status, Task
from task_tui.task_cli import TaskCli


def _make_task(start: datetime | None = None) -> Task:
    now = datetime(2024, 1, 1, 0, 0, 0)
    return Task(
        id=1,
        description="task",
        entry=now.isoformat(),
        modified=now.isoformat(),
        due=None,
        start=start.isoformat() if start else None,
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


def test_start_task_uses_task_cli(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, ...]] = []

    def fake_run(self: TaskCli, *args: str) -> SimpleNamespace:
        calls.append(args)
        return SimpleNamespace(stdout="", returncode=0)

    monkeypatch.setattr(TaskCli, "_run_task", fake_run, raising=False)
    cli = TaskCli()
    task = _make_task()
    calls.clear()

    cli.start_task(task)

    assert calls == [(str(task.uuid), "start")]


def test_stop_task_uses_task_cli(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, ...]] = []

    def fake_run(self: TaskCli, *args: str) -> SimpleNamespace:
        calls.append(args)
        return SimpleNamespace(stdout="", returncode=0)

    monkeypatch.setattr(TaskCli, "_run_task", fake_run, raising=False)
    cli = TaskCli()
    task = _make_task(start=datetime(2024, 1, 1, 12, 0, 0))
    calls.clear()

    cli.stop_task(task)

    assert calls == [(str(task.uuid), "stop")]


def test_modify_task_uses_task_cli(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, ...]] = []

    def fake_run(self: TaskCli, *args: str) -> SimpleNamespace:
        calls.append(args)
        return SimpleNamespace(stdout="", returncode=0, stderr="")

    monkeypatch.setattr(TaskCli, "_run_task", fake_run, raising=False)
    cli = TaskCli()
    task = _make_task()
    calls.clear()

    cli.modify_task(task, "project:Home +tag")

    assert calls == [(str(task.uuid), "modify", "project:Home", "+tag")]


def test_modify_task_raises_on_error(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, ...]] = []

    def fake_run(self: TaskCli, *args: str) -> SimpleNamespace:
        calls.append(args)
        return SimpleNamespace(stdout="", stderr="mod failed", returncode=1)

    monkeypatch.setattr(TaskCli, "_run_task", fake_run, raising=False)
    cli = TaskCli()
    task = _make_task()
    calls.clear()

    with pytest.raises(ValueError, match="mod failed"):
        cli.modify_task(task, "priority:H")

    assert calls == [(str(task.uuid), "modify", "priority:H")]
