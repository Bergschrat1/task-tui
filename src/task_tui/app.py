import logging
from itertools import compress
from typing import Any
from uuid import UUID

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Grid, Horizontal
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Footer, Label

from task_tui.data_models import Task
from task_tui.task import TaskCli

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

task_cli = TaskCli()


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

    def __getattr__(self, attribute_name: str) -> list[Any]:
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

    def __getitem__(self, idx: int) -> Task:
        if not isinstance(idx, int):
            raise IndexError("Index needs to be an integer")
        return self.tasks[idx]

    @property
    def depends(self) -> list[str]:
        ret = []
        for task in self.tasks:
            dep_ids = []
            for uuid in task.depends:
                dep_task = self._get_task_by_uuid(uuid)
                if dep_task is not None:
                    dep_ids.append(str(dep_task.id))
            ret.append(",".join(dep_ids))
        return ret

    @property
    def tags(self) -> list[str]:
        ret = []
        for task in self.tasks:
            ret.append(",".join(task.tags or []))
        return ret


class ConfirmDone(ModalScreen):
    """Screen with a dialog to quit."""

    task_to_complete: Task

    def compose(self) -> ComposeResult:
        yield Grid(
            Label(f'Are you sure you want set task "{self.task_to_complete.description}" ({self.task_to_complete.id}) to done?', id="question"),
            Horizontal(
                Button("Yes", variant="error", id="yes"),
                Button("No", variant="primary", id="no"),
            ),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yes":
            self.dismiss(True)
        else:
            self.app.pop_screen()


class TaskReport(DataTable):
    def on_mount(self) -> None:
        self.cursor_type = "row"
        self.zebra_stripes = True
        self.app._update_table()


class TaskTuiApp(App):
    CSS_PATH = "./TasTuiApp.tscc"
    headings: reactive[list[tuple[str, str]]] = reactive(list())
    tasks = reactive(TaskStore([]), recompose=True)
    report: str
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("d", "set_done", "Set done"),
    ]

    def compose(self) -> ComposeResult:
        yield TaskReport()
        yield Footer()

    def _data_empty(self, data: list[Any]) -> bool:
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

    def _update_tasks(self) -> None:
        """Update the tasks using the task cli.

        NOTE: Updating the task will trigger a table update.
        """
        tasks = task_cli.export_tasks(self.report)
        log.debug(f"Got {len(tasks)} new tasks.")
        self.tasks = TaskStore(tasks)
        self.headings = task_cli.get_report_columns(self.report)

    def _update_table(self) -> None:
        table = self.query_one(TaskReport)
        table.clear()
        columns = [h[0].split(".")[0] for h in self.headings]
        labels = [h[1] for h in self.headings]
        data = [getattr(self.tasks, col) for col in columns]
        columns, labels, data = self._clean_empty_columns(columns, labels, data)
        rows = list(map(list, zip(*data)))
        table.add_columns(*labels)
        table.add_rows(rows)

    def on_mount(self) -> None:
        self._update_tasks()

    def watch_tasks(self) -> None:
        log.debug("Tasks have changed! Updating table")
        self._update_table()

    def action_set_done(self) -> None:
        def check_done(quit: bool | None) -> None:
            if quit:
                task_cli.set_task_done(current_task)
                self._update_tasks()

        table = self.query_one(TaskReport)
        current_task = self.tasks[table.cursor_row]
        confirm_done_scree = ConfirmDone()
        confirm_done_scree.task_to_complete = current_task
        self.push_screen(confirm_done_scree, check_done)
