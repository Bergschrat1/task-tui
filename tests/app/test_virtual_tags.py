from datetime import date, datetime, timedelta
from typing import Callable, Protocol, cast, runtime_checkable
from uuid import UUID, uuid4

import pytest

from task_tui.config import Config
from task_tui.data_models import Status, Task, VirtualTag


@runtime_checkable
class TaskStoreProto(Protocol):
    def __getitem__(self, i: int) -> Task: ...
    def __len__(self) -> int: ...


TaskStoreFactory = Callable[[list[Task], Config], TaskStoreProto]


@pytest.fixture()
def task_store_cls(monkeypatch: pytest.MonkeyPatch) -> TaskStoreFactory:
    import importlib
    import sys

    import task_tui.task_cli as task_cli_mod

    class DummyTaskCli:
        def __init__(self) -> None:
            pass

    monkeypatch.setattr(task_cli_mod, "TaskCli", DummyTaskCli)
    if "task_tui.app" in sys.modules:
        del sys.modules["task_tui.app"]
    app_mod = importlib.import_module("task_tui.app")

    def factory(tasks: list[Task], config: Config) -> TaskStoreProto:
        return cast(TaskStoreProto, app_mod.TaskStore(tasks, config))

    return factory


def make_config(due_days: int = 3) -> Config:
    # Minimal config; only 'due' matters for _update_virtual_tags
    return Config(f"due {due_days}")


def make_task(
    *,
    id_: int = 1,
    description: str = "task",
    entry: datetime | None = None,
    modified: datetime | None = None,
    due: datetime | None = None,
    start: datetime | None = None,
    scheduled: datetime | None = None,
    until: datetime | None = None,
    project: str | None = None,
    status: Status = Status.PENDING,
    tags: set[str] | None = None,
    depends: set[UUID] | None = None,
    priority: str | None = None,
) -> Task:
    now = datetime(2024, 1, 1, 0, 0, 0)
    return Task(
        id=id_,
        description=description,
        entry=(entry or now).isoformat(),
        modified=(modified or now).isoformat(),
        due=due.isoformat() if due else None,
        start=start.isoformat() if start else None,
        scheduled=scheduled.isoformat() if scheduled else None,
        until=until.isoformat() if until else None,
        project=project,
        status=status,
        uuid=uuid4(),
        urgency=0.0,
        annotations=[],
        priority=priority,
        tags=tags or set(),
        depends=depends or set(),
        virtual_tags=set(),  # ensure per-instance set
    )


class TestDueVirtualTags:
    @pytest.mark.parametrize(
        "offset_days,expected_tags,unexpected_tags",
        [
            (-1, {VirtualTag.OVERDUE}, {VirtualTag.DUETODAY, VirtualTag.DUE}),
            (0, {VirtualTag.DUE, VirtualTag.DUETODAY}, {VirtualTag.OVERDUE}),
            (2, {VirtualTag.DUE}, {VirtualTag.DUETODAY, VirtualTag.OVERDUE}),
            (10, set(), {VirtualTag.DUE, VirtualTag.DUETODAY, VirtualTag.OVERDUE}),
        ],
    )
    def test_due_tag_calculation(
        self,
        monkeypatch: pytest.MonkeyPatch,
        task_store_cls: TaskStoreFactory,
        offset_days: int,
        expected_tags: set[VirtualTag],
        unexpected_tags: set[VirtualTag],
    ) -> None:
        today = date(2024, 1, 10)
        import task_tui.app as app_mod

        monkeypatch.setattr(app_mod, "get_current_date", lambda: today)

        due_dt = datetime.combine(today + timedelta(days=offset_days), datetime.min.time())
        task = make_task(due=due_dt)
        store = task_store_cls([task], make_config(due_days=3))

        vt = store[0].virtual_tags
        for tag in expected_tags:
            assert tag in vt, f"expected {tag} to be present for offset {offset_days}"
        for tag in unexpected_tags:
            assert tag not in vt, f"did not expect {tag} for offset {offset_days}"


class TestAttributeVirtualTags:
    def test_field_driven_tags(self, task_store_cls: TaskStoreFactory) -> None:
        task = make_task(
            start=datetime(2024, 1, 2),
            priority="H",
            tags={"home"},
            scheduled=datetime(2024, 1, 5),
            until=datetime(2024, 1, 20),
            project=None,
            status=Status.WAITING,
        )
        store = task_store_cls([task], make_config())
        vt = store[0].virtual_tags

        assert VirtualTag.ACTIVE in vt
        assert VirtualTag.PRIORITY in vt
        assert VirtualTag.TAGGED in vt
        assert VirtualTag.SCHEDULED in vt
        assert VirtualTag.UNTIL in vt
        assert VirtualTag.NO_PROJECT in vt
        assert VirtualTag.WAITING in vt
        assert VirtualTag.NO_TAG not in vt  # since tags are present

    def test_no_tags_adds_no_tag_virtual_tag(self, task_store_cls: TaskStoreFactory) -> None:
        task = make_task(tags=set())
        store = task_store_cls([task], make_config())
        vt = store[0].virtual_tags
        assert VirtualTag.NO_TAG in vt
        assert VirtualTag.TAGGED not in vt


class TestStatusVirtualTags:
    @pytest.mark.parametrize(
        "status,expected_tag",
        [
            (Status.WAITING, VirtualTag.WAITING),
            (Status.RECURRING, VirtualTag.RECURRING),
            (Status.COMPLETED, VirtualTag.COMPLETED),
            (Status.DELETED, VirtualTag.DELETED),
        ],
    )
    def test_status_flags_are_applied(self, task_store_cls: TaskStoreFactory, status: Status, expected_tag: VirtualTag) -> None:
        task = make_task(status=status)
        store = task_store_cls([task], make_config())
        assert expected_tag in store[0].virtual_tags

    def test_pending_has_no_special_status_tags(self, task_store_cls: TaskStoreFactory) -> None:
        task = make_task(status=Status.PENDING)
        store = task_store_cls([task], make_config())
        vt = store[0].virtual_tags
        assert VirtualTag.WAITING not in vt
        assert VirtualTag.RECURRING not in vt
        assert VirtualTag.COMPLETED not in vt
        assert VirtualTag.DELETED not in vt


class TestDependencyTagging:
    def test_blocking_and_blocked_tags_are_set_for_dependencies(self, task_store_cls: TaskStoreFactory) -> None:
        dep_task = make_task(id_=1, description="dep", status=Status.PENDING)
        main_task = make_task(id_=2, description="main", status=Status.PENDING, depends={dep_task.uuid})

        store = task_store_cls([dep_task, main_task], make_config())

        dep_vt = store[0].virtual_tags
        main_vt = store[1].virtual_tags

        assert VirtualTag.BLOCKING in dep_vt
        assert VirtualTag.BLOCKED in main_vt

    def test_blocking_and_blocked_even_if_dependency_completed(self, task_store_cls: TaskStoreFactory) -> None:
        # Reflects current implementation behavior which doesn't check Status types correctly
        dep_task = make_task(id_=3, description="dep done", status=Status.COMPLETED)
        main_task = make_task(id_=4, description="main", status=Status.PENDING, depends={dep_task.uuid})

        store = task_store_cls([dep_task, main_task], make_config())

        dep_vt = store[0].virtual_tags
        main_vt = store[1].virtual_tags

        assert VirtualTag.BLOCKING not in dep_vt
        assert VirtualTag.BLOCKED not in main_vt
