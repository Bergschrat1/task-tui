import logging
from itertools import compress
from typing import Any
from uuid import UUID

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.message import Message
from textual.widgets import Footer

from task_tui.data_models import Task
from task_tui.exceptions import TaskStoreError
from task_tui.task_cli import TaskCli
from task_tui.widgets import ConfirmDialog, TaskReport, TextInput

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

task_cli = TaskCli()


class TaskStore:
    tasks: list[Task]

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

    def __init__(self, tasks: list[Task]) -> None:
        self.tasks = tasks

    def __len__(self) -> int:
        return len(self.tasks)

    def _get_index_by_uuid(self, uuid: UUID) -> int | None:
        ret = [i for i, t in enumerate(self.tasks) if t.uuid == uuid]
        if len(ret) > 1:
            raise TaskStoreError(f"Multiple tasks with the same UUID: {uuid}")
        return ret[0] if ret else None

    def _get_task_by_id(self, id: int) -> Task | None:
        ret = [t for t in self.tasks if t.id == id]
        if len(ret) > 1:
            raise TaskStoreError(f"Multiple tasks with the same ID: {id}")
        return ret[0] if ret else None

    def _get_task_by_uuid(self, uuid: UUID) -> Task | None:
        ret = [t for t in self.tasks if t.uuid == uuid]
        if len(ret) > 1:
            raise TaskStoreError(f"Multiple tasks with the same UUID: {uuid}")
        return ret[0] if ret else None

    def _get_task_column(self, col_name: str) -> list[Any]:
        return [getattr(task, col_name) for task in self.tasks]

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


class TasksChanged(Message):
    def __init__(self, select_task_id: int | None = None) -> None:
        super().__init__()
        self.select_task_id = select_task_id


class TaskTuiApp(App):
    CSS_PATH = "./TasTuiApp.tscc"
    headings: list[tuple[str, str]] = list()
    tasks: TaskStore = TaskStore([])
    report: str
    BINDINGS = [
        Binding("q,escape", "quit", "Quit"),
        Binding("d", "set_done", "Set done"),
        Binding("a", "add_task", "Add task"),
        Binding("r", "refresh_tasks", "Refresh"),
    ]

    def __init__(self, report: str) -> None:
        self.report = report
        super().__init__()

    def compose(self) -> ComposeResult:
        yield TaskReport()
        yield Footer()

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

    def _data_empty(self, data: list[Any]) -> bool:
        return all(v in ("", None, []) for v in data)

    def _update_table(self) -> None:
        log.debug("Updating table")
        table = self.query_one(TaskReport)
        table.clear(columns=True)
        columns = [h[0].split(".")[0] for h in self.headings]
        labels = [h[1] for h in self.headings]
        data = [getattr(self.tasks, col) for col in columns]
        columns, labels, data = self._clean_empty_columns(columns, labels, data)
        rows = list(map(list, zip(*data)))
        table.add_columns(*labels)
        table.add_rows(rows)

    @on(TasksChanged)
    async def _update_tasks(self, event: TasksChanged) -> None:
        """Update the tasks using the task cli.

        NOTE: Updating the task will trigger a table update.
        """
        table = self.query_one(TaskReport)
        previous_row: int = table.cursor_row
        log.debug("Updating tasks")
        log.debug("Previous row: %d, Previous number of tasks: %d", previous_row, len(self.tasks))
        tasks = task_cli.export_tasks(self.report)
        self.tasks = TaskStore(tasks)
        self.headings = task_cli.get_report_columns(self.report)
        self._update_table()

        if event.select_task_id is not None:
            try:
                task = self.tasks._get_task_by_id(event.select_task_id)
                select_task_index = self.tasks._get_index_by_uuid(task.uuid)
            except TaskStoreError as e:
                log.error("Failed to get task by id: %s", e)
                self.notify("Failed to select task with id: %s", event.select_task_id)
                select_task_index = 0
        else:
            select_task_index = previous_row
        # move_cursor already handles upper out-of-bounds by selecting the highest available row so this is not handled manually
        table.move_cursor(row=select_task_index, animate=True, scroll=True)

    def on_mount(self) -> None:
        log.debug("Mounting app")
        self.post_message(TasksChanged())

    def action_add_task(self) -> None:
        def add_task(description: str) -> None:
            try:
                new_task_id = task_cli.add_task(description)
            except ValueError as e:
                self.notify(f"Failed to create task:\n{str(e)}", severity="error", markup=True)
                return
            self.post_message(TasksChanged(select_task_id=new_task_id))

        add_task_screen = TextInput("Enter task description")
        self.push_screen(add_task_screen, add_task)

    def action_quit(self) -> None:
        # confirm_quit_sqreen = ConfirmDialog("Are you sure you want to quit?")
        # self.push_screen(confirm_quit_sqreen, self.exit)
        log.debug("Quitting app")
        self.exit()

    def action_refresh_tasks(self) -> None:
        log.debug("Refreshing tasks")
        self.post_message(TasksChanged())
        self.notify("Tasks refreshed")

    def action_set_done(self) -> None:
        def set_done(quit: bool | None) -> None:
            task_cli.set_task_done(current_task)
            self.post_message(TasksChanged())

        table = self.query_one(TaskReport)
        current_task = self.tasks[table.cursor_row]
        confirm_done_scree = ConfirmDialog(f'Are you sure you want set task "{current_task.description}" ({current_task.id}) to done?')
        self.push_screen(confirm_done_scree, set_done)
