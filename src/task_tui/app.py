import logging
from itertools import compress
from typing import Any
from uuid import UUID

from textual.app import App, ComposeResult
from textual.reactive import reactive
from textual.widgets import DataTable

from task_tui.data_models import Task

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class TaskStore:
    tasks: list[Task]

    def __init__(self, tasks: list[Task]) -> None:
        self.tasks = tasks

    def _get_task_by_uuid(self, uuid: UUID) -> Task | None:
        ret = [t for t in self.tasks if t.uuid == uuid]
        if len(ret) > 1:
            raise ValueError(f"Multiple tasks with the same UUID: {uuid}")
        return ret[0] if ret else None

    def _get_task_column(self, col_name: str) -> list[Any]:
        return [getattr(task, col_name) for task in self.tasks]

    def __getattr__(self, attribute_name: str):
        if attribute_name not in Task.model_fields:
            msg = "'{0}': object has no attribute '{1}'"
            raise AttributeError(msg.format(type(self).__name__, attribute_name))
        try:
            # if there is a special formatting function for this attribute we use that
            ret = self.__getattribute__(attribute_name)
        except AttributeError:
            # otherwise we use the unprocessed values
            ret = self._get_task_column(attribute_name)

        return ret

    @property
    def depends(self):
        ret = []
        for task in self.tasks:
            dep_ids = []
            for uuid in task.depends:
                dep_task = self._get_task_by_uuid(uuid)
                if dep_task is not None:
                    dep_ids.append(str(dep_task.id))
            ret.append(",".join(dep_ids))
        return ret


class TaskReport(DataTable):
    pass


class TaskTuiApp(App):
    headings: reactive[list[tuple[str, str]]] = reactive(list())
    # tasks: reactive[list[Task]] = reactive(list())
    tasks: TaskStore

    def compose(self) -> ComposeResult:
        yield TaskReport()

    def _data_empty(self, data) -> bool:
        return all(v in ("", None, []) for v in data)

    def _clean_empty_columns(
        self,
        columns: list[str],
        labels: list[str],
        data: list[Any],
    ) -> tuple[list[str], list[str], list[Any]]:
        keep = [not self._data_empty(d) for d in data]
        return (
            list(compress(columns, keep)),
            list(compress(labels, keep)),
            list(compress(data, keep)),
        )

    def on_mount(self):
        table = self.query_one(TaskReport)
        columns = [h[0].split(".")[0] for h in self.headings]
        labels = [h[1] for h in self.headings]
        data = [getattr(self.tasks, col) for col in columns]
        columns, labels, data = self._clean_empty_columns(columns, labels, data)
        rows = list(map(list, zip(*data)))
        table.add_columns(*labels)
        table.add_rows(rows)
