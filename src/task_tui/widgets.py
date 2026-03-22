import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

from rich.style import Style
from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Grid
from textual.coordinate import Coordinate
from textual.events import Key
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Footer, Input, Label
from textual.widgets.data_table import CursorType, RowKey

from task_tui.data_models import ContextInfo, Status, Task
from task_tui.utils import format_vague_datetime, get_current_datetime

log = logging.getLogger(__name__)


class MouseOnlyButton(Button):
    # Prevent keyboard focus and key activation; still clickable with mouse
    can_focus = False

    def key_enter(self) -> None:
        pass

    def key_space(self) -> None:
        pass


class ConfirmDialog(ModalScreen):
    """Screen with a dialog to confirm an action."""

    BINDINGS = [
        Binding("enter,y", "confirm", "Confirm"),
        Binding("escape,n", "cancel", "Cancel"),
    ]

    def __init__(self, prompt: str) -> None:
        self.prompt = prompt
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Grid(
            Label(self.prompt, id="question"),
            Footer(),
            id="dialog",
        )

    def action_confirm(self) -> None:
        log.debug('Confirmed prompt "%s"', self.prompt)
        self.dismiss(True)

    def action_cancel(self) -> None:
        log.debug('Cancelled prompt "%s"', self.prompt)
        self.app.pop_screen()


class BubblingEnterInput(Input):
    def on_key(self, event: Key) -> None:
        if event.key == "enter":
            event.prevent_default()


class TextInput(ModalScreen):
    prompt: str
    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("enter", "submit", "Submit", priority=True),
    ]

    def __init__(self, prompt: str) -> None:
        self.prompt = prompt
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Grid(
            Label(self.prompt, id="question"),
            BubblingEnterInput(id="input", type="text"),
            Footer(),
            id="dialog",
        )

    def action_submit(self) -> None:
        input_text = self.query_one("#input").value
        log.debug('Submitted input: "%s"', input_text)
        self.dismiss(input_text)

    def action_cancel(self) -> None:
        self.app.pop_screen()


class RowMarkerTable(DataTable):
    """DataTable variant that shows a single-row marker instead of cell highlights.

    Used by tables that want a consistent, cursor-driven row indicator (▶) so
    selection remains visible while avoiding Textual's default cell highlight.
    """

    def __init__(self) -> None:
        super().__init__()
        self.show_row_labels = True
        self.cursor_type = "row"
        self._marker_row_key: RowKey | None = None
        self.cursor_background_priority = "renderable"
        self.cursor_foreground_priority = "renderable"

    def _set_row_marker(self, row_key: RowKey, symbol: str) -> int | None:
        row = self.rows.get(row_key)
        if row is None:
            return None
        row.label = Text(symbol or " ")
        if symbol:
            self._labelled_row_exists = True
        row_index = self._row_locations.get(row_key)
        return row_index

    def clear_selection_marker(self) -> None:
        if self._marker_row_key is None:
            return
        row_index = self._set_row_marker(self._marker_row_key, "")
        self._marker_row_key = None
        if row_index is not None and self.is_valid_row_index(row_index):
            self._update_count += 1
            self.refresh_row(row_index)

    def _apply_marker_update(self, target_row_index: int | None) -> None:
        rows_to_refresh: list[int] = []
        if self._marker_row_key is not None:
            previous_index = self._set_row_marker(self._marker_row_key, "")
            self._marker_row_key = None
            if previous_index is not None and self.is_valid_row_index(previous_index):
                rows_to_refresh.append(previous_index)

        if target_row_index is not None and target_row_index >= 0 and target_row_index < self.row_count:
            row_key = self._row_locations.get_key(target_row_index)
            if row_key is not None:
                current_index = self._set_row_marker(row_key, "▶")
                self._marker_row_key = row_key
                if current_index is not None and self.is_valid_row_index(current_index):
                    rows_to_refresh.append(current_index)

        if rows_to_refresh:
            # increment _update_count to invalidate the row_cache (which will trigger a redraw)
            self._update_count += 1
            for row_index in rows_to_refresh:
                self.refresh_row(row_index)

    def watch_cursor_coordinate(self, old_coordinate: Coordinate, new_coordinate: Coordinate) -> None:
        self._apply_marker_update(new_coordinate.row if self.row_count else None)
        super().watch_cursor_coordinate(old_coordinate, new_coordinate)

    def sync_cursor_marker(self) -> None:
        if self.row_count == 0:
            self._marker_row_key = None
            return
        self._apply_marker_update(self.cursor_coordinate.row)

    def _should_highlight(
        self,
        cursor: Coordinate,
        target_cell: Coordinate,
        type_of_cursor: CursorType,
    ) -> bool:
        # overwrite the _should_highlight function to always return false. We only want to use the marker
        return False


class TaskReport(RowMarkerTable):
    BINDINGS = [
        Binding("j", "cursor_down", "Cursor Down", show=False),
        Binding("k", "cursor_up", "Cursor Up", show=False),
        Binding("ctrl+d", "page_down", "Page Down", show=False),
        Binding("ctrl+u", "page_up", "Page Up", show=False),
        Binding("G", "page_up", "Page Up", show=False),
        Binding("a", "add_task", "Add task"),
        Binding("d", "set_done", "Set done"),
        Binding("delete", "delete_task", "Delete task"),
        Binding("m", "modify_task", "Modify task"),
        Binding("A", "annotate_task", "Annotate"),
        Binding("r", "refresh_tasks", "Refresh"),
        Binding("s", "toggle_start_stop", "Start/stop"),
        Binding("l", "log_task", "Log task"),
        Binding("e", "edit_task", "Edit task"),
        Binding("R", "start_review", "Review tasks"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._row_style_overrides: dict[int, Style] = {}
        self.zebra_stripes = True

    def on_mount(self) -> None:
        log.debug("TaskReport mounted")
        self.cursor_type = "row"
        self.zebra_stripes = True
        self.app._update_table()

    def action_add_task(self) -> None:
        self.app.action_add_task()

    def action_set_done(self) -> None:
        self.app.action_set_done()

    def action_delete_task(self) -> None:
        self.app.action_delete_task()

    def action_modify_task(self) -> None:
        self.app.action_modify_task()

    def action_annotate_task(self) -> None:
        self.app.action_annotate_task()

    def action_refresh_tasks(self) -> None:
        self.app.action_refresh_tasks()

    def action_toggle_start_stop(self) -> None:
        self.app.action_toggle_start_stop()

    def action_log_task(self) -> None:
        self.app.action_log_task()

    def action_edit_task(self) -> None:
        self.app.action_edit_task()

    def action_start_review(self) -> None:
        self.app.action_start_review()

    def set_row_style(self, index: int, style: Style) -> None:
        self._row_style_overrides[index] = style
        self.refresh_row(index)

    def clear_row_styles(self) -> None:
        self._row_style_overrides.clear()

    def _get_row_style(self, row_index: int, base_style: Style) -> Style:
        if row_index in self._row_style_overrides:
            return self._row_style_overrides[row_index]
        return super()._get_row_style(row_index, base_style)


@dataclass
class ProjectAggregate:
    total: int = 0
    pending: int = 0
    completed: int = 0
    urgency: float = 0.0


class ProjectSummary(DataTable):
    def __init__(self) -> None:
        super().__init__()
        self.cursor_type = "row"
        self.show_row_labels = False
        self.zebra_stripes = True

    def on_mount(self) -> None:
        self.clear(columns=True)
        self.add_columns("Project", "Remaining", "Completed", "Urgency Sum")

    def refresh_from_tasks(self, tasks: Iterable[Task]) -> None:
        aggregates: dict[str, ProjectAggregate] = defaultdict(ProjectAggregate)
        for task in tasks:
            project_name = task.project or "(none)"
            aggregate = aggregates[project_name]
            aggregate.total += 1
            if task.status == Status.COMPLETED:
                aggregate.completed += 1
            elif task.status != Status.DELETED:
                aggregate.pending += 1
            aggregate.urgency += task.urgency

        self.clear(columns=False)
        for project_name in sorted(aggregates):
            aggregate = aggregates[project_name]
            if aggregate.pending < 1:  # don't include completed projects
                continue
            self.add_row(
                project_name,
                aggregate.pending,
                f"{int(aggregate.completed / (aggregate.completed + aggregate.pending) * 100)}%",
                f"{aggregate.urgency:.2f}",
            )
        self.refresh()


class ContextSelected(Message):
    def __init__(self, context: ContextInfo) -> None:
        super().__init__()
        self.context = context


class ContextSummary(RowMarkerTable):
    BINDINGS = [
        Binding("j", "cursor_down", "Cursor Down", show=False),
        Binding("k", "cursor_up", "Cursor Up", show=False),
        Binding("enter", "select_context", "Select context"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.zebra_stripes = True
        self._contexts: list[ContextInfo] = []

    def on_mount(self) -> None:
        self.clear(columns=True)
        self.add_columns("Context", "Filter")

    def refresh_from_contexts(self, contexts: Iterable[ContextInfo]) -> None:
        self._contexts = list(contexts)
        self.clear(columns=False)
        for context in self._contexts:
            label = f"{context.name} *" if context.is_active else context.name
            self.add_row(label, context.read_filter)
        self.sync_cursor_marker()
        self.refresh()

    def action_select_context(self) -> None:
        if self.row_count == 0:
            return
        row_index = self.cursor_coordinate.row
        if row_index < 0 or row_index >= len(self._contexts):
            return
        self.post_message(ContextSelected(self._contexts[row_index]))


class ReviewTaskAction(Message):
    """Message sent when a task action is performed in the review dialog."""

    def __init__(self, action: str, task: Task) -> None:
        super().__init__()
        self.action = action
        self.task = task


class ReviewDialogClosed(Message):
    """Message sent when the review dialog is closed."""

    pass


class ReviewDialog(ModalScreen):
    """Modal screen for reviewing tasks one by one."""

    BINDINGS = [
        Binding("enter,r", "mark_reviewed", "Mark reviewed"),
        Binding("s", "skip", "Skip"),
        Binding("e", "edit", "Edit"),
        Binding("m", "modify", "Modify"),
        Binding("c", "complete", "Complete"),
        Binding("d", "delete", "Delete"),
        Binding("q,escape", "quit_review", "Quit"),
    ]

    def __init__(self, tasks: list[Task]) -> None:
        super().__init__()
        self._tasks = tasks
        self._current_index = 0

    def compose(self) -> ComposeResult:
        yield Grid(
            Label("", id="review-title"),
            Label("", id="review-description"),
            Label("", id="review-project"),
            Label("", id="review-due"),
            Label("", id="review-tags"),
            Label("", id="review-urgency"),
            Label("", id="review-reviewed"),
            Label("", id="review-help"),
            Footer(),
            id="review-dialog",
        )

    def on_mount(self) -> None:
        self._update_display()

    def _update_display(self) -> None:
        if self._current_index >= len(self._tasks):
            self.dismiss()
            return

        task = self._tasks[self._current_index]
        now = get_current_datetime()

        self.query_one("#review-title", Label).update(f"Review Tasks ({self._current_index + 1}/{len(self._tasks)})")
        self.query_one("#review-description", Label).update(f"Description: {task.description}")
        self.query_one("#review-project", Label).update(f"Project: {task.project or '(none)'}")
        self.query_one("#review-due", Label).update(f"Due: {format_vague_datetime(task.due, now) if task.due else '(none)'}")
        self.query_one("#review-tags", Label).update(f"Tags: {', '.join(task.tags) if task.tags else '(none)'}")
        self.query_one("#review-urgency", Label).update(f"Urgency: {task.urgency:.1f}")
        reviewed_str = format_vague_datetime(task.reviewed, now) if task.reviewed else "(never)"
        self.query_one("#review-reviewed", Label).update(f"Last Review: {reviewed_str}")
        self.query_one("#review-help", Label).update("(r) Review  (s) Skip  (e) Edit  (m) Modify  (c) Complete  (d) Delete  (q) Quit")

    @property
    def current_task(self) -> Task:
        return self._tasks[self._current_index]

    def action_mark_reviewed(self) -> None:
        log.debug("Marking task %s as reviewed", self.current_task.id)
        self.post_message(ReviewTaskAction("reviewed", self.current_task))
        self._advance()

    def action_skip(self) -> None:
        log.debug("Skipping task %s", self.current_task.id)
        self._advance()

    def action_edit(self) -> None:
        log.debug("Editing task %s", self.current_task.id)
        self.post_message(ReviewTaskAction("edit", self.current_task))

    def action_modify(self) -> None:
        log.debug("Modifying task %s", self.current_task.id)
        self.post_message(ReviewTaskAction("modify", self.current_task))

    def action_complete(self) -> None:
        log.debug("Completing task %s", self.current_task.id)
        self.post_message(ReviewTaskAction("complete", self.current_task))
        self._remove_current_and_continue()

    def action_delete(self) -> None:
        log.debug("Deleting task %s", self.current_task.id)
        self.post_message(ReviewTaskAction("delete", self.current_task))
        self._remove_current_and_continue()

    def action_quit_review(self) -> None:
        log.debug("Quitting review")
        self.post_message(ReviewDialogClosed())
        self.dismiss()

    def _advance(self) -> None:
        self._current_index += 1
        if self._current_index >= len(self._tasks):
            self.post_message(ReviewDialogClosed())
            self.dismiss()
        else:
            self._update_display()

    def _remove_current_and_continue(self) -> None:
        """Remove the current task from the list and continue to the next."""
        self._tasks.pop(self._current_index)
        if self._current_index >= len(self._tasks):
            if len(self._tasks) == 0:
                self.post_message(ReviewDialogClosed())
                self.dismiss()
            else:
                self._current_index = len(self._tasks) - 1
                self._update_display()
        else:
            self._update_display()

    def refresh_current_task(self, updated_task: Task) -> None:
        """Update the current task with refreshed data and redisplay."""
        log.debug("Refreshing current task")
        if self._current_index < len(self._tasks):
            self._tasks[self._current_index] = updated_task
            self._update_display()
