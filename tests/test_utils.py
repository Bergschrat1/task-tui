from datetime import datetime
from typing import Iterable, Set, cast
from uuid import UUID

from rich.color import Color
from rich.style import Style

from task_tui.config import Config
from task_tui.data_models import Status, Task, VirtualTag
from task_tui.utils import get_style_for_task


def make_config(color_lines: Iterable[str], precedence: str) -> Config:
    # Avoid blank or malformed lines; Config._get_config expects key and value on each line
    cfg_str = "\n".join(
        [
            f"rule.precedence.color {precedence}",
            *color_lines,
        ]
    )
    return Config(cfg_str)


def make_task_with_tags(tags: Set[VirtualTag]) -> Task:
    now = datetime(2024, 1, 1, 0, 0, 0)
    return Task(
        id=1,
        description="style test",
        entry=cast(datetime, now.isoformat()),
        modified=cast(datetime, now.isoformat()),
        status=Status.PENDING,
        uuid=UUID("00000000-0000-0000-0000-000000000001"),
        urgency=0.0,
        annotations=[],
        tags=set(),
        depends=set(),
        virtual_tags=set(tags),
    )


class TestGetStyleForTask:
    def test_only_configured_tags_contribute(self) -> None:
        # Task has OVERDUE and PRIORITY tags, but config only defines OVERDUE
        config = make_config(
            color_lines=[
                "color.overdue red",
            ],
            precedence="overdue,priority",
        )
        task = make_task_with_tags({VirtualTag.OVERDUE, VirtualTag.PRIORITY})

        style = get_style_for_task(task, config)
        assert style == Style(color=Color.from_ansi(1))  # red

    def test_precedence_ordering(self) -> None:
        # due.today should win over overdue according to precedence
        config = make_config(
            color_lines=[
                "color.overdue red",
                "color.due.today blue",
            ],
            precedence="due.today,overdue",
        )
        task = make_task_with_tags({VirtualTag.OVERDUE, VirtualTag.DUETODAY})

        style = get_style_for_task(task, config)
        assert style == Style(color=Color.from_ansi(4))  # blue

    def test_style_merge_of_multiple_attributes(self) -> None:
        # overdue provides bold+fg red, blocked provides underline+bg blue
        # precedence: blocked,overdue => overdue applied first, then blocked overlays underline/bg
        config = make_config(
            color_lines=[
                "color.overdue bold red",
                "color.blocked underline on blue",
            ],
            precedence="blocked,overdue",
        )
        task = make_task_with_tags({VirtualTag.OVERDUE, VirtualTag.BLOCKED})

        style = get_style_for_task(task, config)
        # Expect fg red from overdue, plus underline True and bg blue from blocked, bold preserved
        assert style == Style(
            color=Color.from_ansi(1),
            bgcolor=Color.from_ansi(4),
            underline=True,
            bold=True,
        )

    def test_no_matching_tags_returns_default_style(self) -> None:
        config = make_config(
            color_lines=[
                "color.overdue red",
                "color.due.today blue",
            ],
            precedence="due.today,overdue",
        )
        # No virtual tags match configured entries
        task = make_task_with_tags(set())

        style = get_style_for_task(task, config)
        assert style == Style()
