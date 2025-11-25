import types
from datetime import datetime, timedelta
from uuid import UUID

import pytest

from task_tui.config import Config
from task_tui.data_models import Status, Task


def make_task(
    *,
    task_id: int,
    description: str,
    entry: datetime,
    modified: datetime,
    due: datetime | None,
    start: datetime | None,
    reference_uuid: str,
) -> Task:
    return Task(
        id=task_id,
        description=description,
        entry=entry.isoformat(),
        modified=modified.isoformat(),
        due=due.isoformat() if due else None,
        start=start.isoformat() if start else None,
        scheduled=None,
        wait=None,
        end=None,
        until=None,
        recur=None,
        project=None,
        status=Status.PENDING,
        uuid=UUID(reference_uuid),
        urgency=0.0,
        annotations=[],
        priority=None,
        tags=set(),
        depends=set(),
        virtual_tags=set(),
    )


def test_task_store_formats_vague_dates(app_module_mock: types.ModuleType, monkeypatch: pytest.MonkeyPatch) -> None:
    reference = datetime(2024, 1, 1, 12, 0, 0)
    monkeypatch.setattr(app_module_mock, "get_current_datetime", lambda: reference)

    tasks = [
        make_task(
            task_id=1,
            description="future due",
            entry=reference - timedelta(hours=3),
            modified=reference,
            due=reference + timedelta(days=21),
            start=reference - timedelta(hours=1),
            reference_uuid="00000000-0000-0000-0000-000000000001",
        ),
        make_task(
            task_id=2,
            description="no due",
            entry=reference - timedelta(days=400),
            modified=reference - timedelta(days=1),
            due=None,
            start=None,
            reference_uuid="00000000-0000-0000-0000-000000000002",
        ),
    ]

    task_store = getattr(app_module_mock, "TaskStore")(tasks, Config(""))

    assert task_store.entry == ["-3h", "-1.1y"]
    assert task_store.due == ["3w", ""]
    assert task_store.start == ["-1h", ""]
    assert task_store.modified == ["", "-1d"]
