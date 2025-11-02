from rich.style import Style

from task_tui.config import Config
from task_tui.data_models import Tag, Task


def get_style_for_task(task: Task, config: Config) -> Style:
    if Tag.ACTIVE in task.tags and "active" in config.color:
        return config.color["active"]
    return Style()
