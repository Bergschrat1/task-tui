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
