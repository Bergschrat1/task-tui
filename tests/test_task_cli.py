from datetime import datetime
from types import SimpleNamespace
from typing import cast
from uuid import uuid4

import pytest

from task_tui.data_models import Status, Task
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
    assert calls[1] == (str(task.id), "delete")
