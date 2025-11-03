import logging

from rich.style import Style
from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Grid
from textual.events import Key
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Footer, Input, Label
from textual.widgets.data_table import RowKey

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


class TaskReport(DataTable):
    BINDINGS = [
        Binding("j", "cursor_down", "Cursor Down", show=False),
        Binding("k", "cursor_up", "Cursor Up", show=False),
        Binding("ctrl+d", "page_down", "Page Down", show=False),
        Binding("ctrl+u", "page_up", "Page Up", show=False),
        Binding("G", "page_up", "Page Up", show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._row_style_overrides: dict[int, Style] = {}
        self.show_row_labels = True
        # self.selection_style = Style(bgcolor="default")
        self._marker_row_key: RowKey | None = None

    def _set_row_marker(self, row_key: RowKey, symbol: str) -> None:
        row = self.rows.get(row_key)
        if row is None:
            return
        row_index = self._row_locations.get(row_key)
        log.debug('Setting row marker of row %d to "%s"', row_index, symbol)
        label_text = Text(symbol) if symbol else Text(" ")
        row.label = label_text
        if row_index is not None:
            self.refresh_row(row_index)

    def clear_selection_marker(self) -> None:
        log.debug("Clearing selection marker.")
        if self._marker_row_key is None:
            return
        self._set_row_marker(self._marker_row_key, "")
        row_index = self._row_locations.get(self._marker_row_key)
        if row_index is not None:
            self.refresh_row(row_index)
        self._marker_row_key = None

    @on(DataTable.RowHighlighted)
    def watch_cursor_row(self, event: DataTable.RowHighlighted) -> None:
        cursor_row = event.cursor_row
        log.debug("Row %d was selected", cursor_row)
        if self._marker_row_key is not None:
            self.clear_selection_marker()
        if cursor_row < 0 or cursor_row >= self.row_count:
            return
        row_key = self._row_locations.get_key(cursor_row)
        if row_key is None:
            return
        self._set_row_marker(row_key, "▶")
        self._marker_row_key = row_key

    def sync_cursor_marker(self) -> None:
        if self.row_count == 0:
            self._marker_row_key = None
            return
        # self.watch_cursor_row(self.cursor_row)

    def on_mount(self) -> None:
        log.debug("TaskReport mounted")
        self.cursor_type = "row"
        self.zebra_stripes = True
        self.app._update_table()

    def set_row_style(self, index: int, style: Style) -> None:
        self._row_style_overrides[index] = style
        self.refresh_row(index)

    def clear_row_styles(self) -> None:
        self._row_style_overrides.clear()

    def _get_row_style(self, row_index: int, base_style: Style) -> Style:
        if row_index in self._row_style_overrides:
            return self._row_style_overrides[row_index]
        return super()._get_row_style(row_index, base_style)
