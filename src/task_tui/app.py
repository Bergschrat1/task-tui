from textual.app import App, ComposeResult
from textual.reactive import reactive
from textual.widgets import DataTable

from task_tui.data_models import Task


class TaskReport(DataTable):
    pass


class TaskTuiApp(App):
    headings: reactive[list[tuple[str, str]]] = reactive(list())
    tasks: reactive[list[Task]] = reactive(list())

    def compose(self) -> ComposeResult:
        yield TaskReport()

    def on_mount(self):
        table = self.query_one(TaskReport)
        heading_labels = [h[1] for h in self.headings]
        heading_columns = [h[0].split(".")[0] for h in self.headings]
        table.add_columns(*heading_labels)
        data = [[getattr(task, col) for col in heading_columns] for task in self.tasks]
        table.add_rows(data)
