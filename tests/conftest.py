import importlib
import sys
import types

import pytest

import task_tui.task_cli as task_cli_mod


@pytest.fixture()
def app_module_mock(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    class DummyTaskCli:
        def __init__(self) -> None:
            pass

    monkeypatch.setattr(task_cli_mod, "TaskCli", DummyTaskCli)
    if "task_tui.app" in sys.modules:
        del sys.modules["task_tui.app"]

    return importlib.import_module("task_tui.app")
