from rich.style import Style

from task_tui.config import Config
from task_tui.data_models import Task, VirtualTag


def get_style_for_task(task: Task, config: Config) -> Style:
    if VirtualTag.ACTIVE in task.virtual_tags and "active" in config.color:
        return config.color["active"]
    # TODO add remaining tags
    return Style()
