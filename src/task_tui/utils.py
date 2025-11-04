from rich.style import Style

from task_tui.config import Config
from task_tui.data_models import Task, VirtualTag


def get_style_for_task(task: Task, config: Config) -> Style:
    styles_to_apply = []

    if VirtualTag.ACTIVE in task.virtual_tags and "active" in config.color:
        styles_to_apply.append(config.color["active"])
    if VirtualTag.BLOCKED in task.virtual_tags and "blocked" in config.color:
        styles_to_apply.append(config.color["blocked"])
    if VirtualTag.BLOCKING in task.virtual_tags and "blocking" in config.color:
        styles_to_apply.append(config.color["blocking"])
    if VirtualTag.COMPLETED in task.virtual_tags and "completed" in config.color:
        styles_to_apply.append(config.color["completed"])
    if VirtualTag.DELETED in task.virtual_tags and "deleted" in config.color:
        styles_to_apply.append(config.color["deleted"])
    if VirtualTag.DUE in task.virtual_tags and "due" in config.color:
        styles_to_apply.append(config.color["due"])
    if VirtualTag.DUETODAY in task.virtual_tags and "due.today" in config.color:
        styles_to_apply.append(config.color["due.today"])
    if VirtualTag.OVERDUE in task.virtual_tags and "overdue" in config.color:
        styles_to_apply.append(config.color["overdue"])
    if VirtualTag.RECURRING in task.virtual_tags and "recurring" in config.color:
        styles_to_apply.append(config.color["recurring"])
    if VirtualTag.SCHEDULED in task.virtual_tags and "scheduled" in config.color:
        styles_to_apply.append(config.color["scheduled"])
    if VirtualTag.TAGGED in task.virtual_tags and "tagged" in config.color:
        styles_to_apply.append(config.color["tagged"])
    if VirtualTag.UNTIL in task.virtual_tags and "until" in config.color:
        styles_to_apply.append(config.color["until"])
    if VirtualTag.NO_PROJECT in task.virtual_tags and "project.none" in config.color:
        styles_to_apply.append(config.color["project.none"])
    if VirtualTag.NO_TAG in task.virtual_tags and "tag.none" in config.color:
        styles_to_apply.append(config.color["tag.none"])
    # TODO add blocking/blocked
    # TODO add due/overdue/duetoday
    #
    #
    # TODO aggregate styles_to_apply
    ## let virtual_tags = vec![
    # "PROJECT",
    # "BLOCKED",
    # "UNBLOCKED",
    # "BLOCKING",
    # "DUE",
    # "DUETODAY",
    # "TODAY",
    # "OVERDUE",
    # "WEEK",
    # "MONTH",
    # "QUARTER",
    # "YEAR",
    # "ACTIVE",
    # "SCHEDULED",
    # "PARENT",
    # "CHILD",
    # "UNTIL",
    # "WAITING",
    # "ANNOTATED",
    # "READY",
    # "YESTERDAY",
    # "TOMORROW",
    # "TAGGED",
    # "PENDING",
    # "COMPLETED",
    # "DELETED",
    # "UDA",
    # "ORPHAN",
    # "PRIORITY",
    # "PROJECT",
    # "LATEST",
    # "RECURRING",
    # "INSTANCE",
    # "TEMPLATE",
    # ];
    return Style()
