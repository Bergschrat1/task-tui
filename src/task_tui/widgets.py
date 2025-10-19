import logging

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Grid
from textual.events import Key
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Footer, Input, Label

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
    def on_mount(self) -> None:
        log.debug("TaskReport mounted")
        self.cursor_type = "row"
        self.zebra_stripes = True
        self.app._update_table()
