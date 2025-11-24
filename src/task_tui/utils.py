import logging
from datetime import date, datetime

from rich.style import Style

from task_tui.config import Config
from task_tui.data_models import Task, VirtualTag

log = logging.getLogger(__name__)


def get_style_for_task(task: Task, config: Config) -> Style:
    precedence_style_map: dict[str, Style] = {}

    for tag in VirtualTag:
        if tag in task.virtual_tags and tag.value in config.color:
            precedence_style_map[tag.value] = config.color[tag.value]
    # TODO handle uda. project. and tag. color configurations

    ret = Style()
    style_order = [s.strip(".") for s in config.color_precedence.split(",")[::-1]]
    for style_name in style_order:
        if style_name in precedence_style_map:
            ret += precedence_style_map[style_name]

    log.debug("Final style for task %s: %s", task.id, ret)
    return ret


def get_current_datetime() -> datetime:
    return datetime.now()


def get_current_date() -> date:
    return date.today()


def format_vague_duration(seconds: float) -> str:
    sign = "-" if seconds < 0 else ""
    seconds = abs(seconds)
    days = seconds / 86400

    if seconds >= 86400 * 365:
        value = f"{days / 365:.1f}y"
    elif seconds >= 86400 * 90:
        value = f"{int(days / 30)}mo"
    elif seconds >= 86400 * 14:
        value = f"{int(days / 7)}w"
    elif seconds >= 86400:
        value = f"{int(days)}d"
    elif seconds >= 3600:
        value = f"{int(seconds / 3600)}h"
    elif seconds >= 60:
        value = f"{int(seconds / 60)}min"
    elif seconds >= 1:
        value = f"{int(seconds)}s"
    else:
        value = ""

    return f"{sign}{value}" if value else value


def format_vague_datetime(target: datetime | None, reference: datetime | None = None) -> str:
    if target is None:
        return ""

    ref = reference or get_current_datetime()
    delta_seconds = (target - ref).total_seconds()
    return format_vague_duration(delta_seconds)
