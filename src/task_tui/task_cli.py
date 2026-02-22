import logging
import re
import shlex
import subprocess

from task_tui.config import Config
from task_tui.data_models import ContextInfo, Task

log = logging.getLogger(__name__)


class TaskCli:
    base_command: str = "task"

    def __init__(self) -> None:
        try:
            self._run_task("show")
        except FileNotFoundError:
            raise FileNotFoundError("The task CLI tool doesn't seem to be installed.")
        except Exception:
            raise Exception("Could not run `task show`")

    def _run_task(self, *args: str) -> subprocess.CompletedProcess:
        command = [self.base_command, *args]
        log.debug("Running `%s`", " ".join(command))
        return subprocess.run(command, text=True, capture_output=True)

    def _get_config_value(self, config_key: str) -> str:
        completed_process = self._run_task("_get", config_key)
        return completed_process.stdout.strip()

    def _get_context_filter(self, context_name: str) -> str:
        context_filter = self._get_config_value(f"rc.context.{context_name}.read")
        if context_filter == "":
            context_filter = self._get_config_value(f"rc.context.{context_name}")
        return context_filter

    def _parse_context_list(self, context_output: str) -> list[str]:
        contexts: list[str] = []
        for raw_line in context_output.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line not in contexts:
                contexts.append(line)
        return contexts

    def get_context(self) -> ContextInfo | None:
        context_name = self._get_config_value("rc.context")
        if context_name in {"", "none"}:
            return None
        context_filter = self._get_context_filter(context_name)
        return ContextInfo(name=context_name, read_filter=context_filter, is_active=True)

    def list_contexts(self) -> list[ContextInfo]:
        active_context = self._get_config_value("rc.context")
        if active_context == "none":
            active_context = ""
        context_output = self._run_task("_context").stdout
        context_names = self._parse_context_list(context_output)
        contexts: list[ContextInfo] = []
        contexts.append(ContextInfo(name="none", read_filter="", is_active=active_context == ""))
        for context_name in context_names:
            if context_name == "none":
                continue
            context_filter = self._get_context_filter(context_name)
            contexts.append(
                ContextInfo(
                    name=context_name,
                    read_filter=context_filter,
                    is_active=context_name == active_context,
                )
            )
        return contexts

    def set_context(self, context_name: str | None) -> None:
        if context_name is None or context_name == "none":
            self._run_task("context", "none")
        else:
            self._run_task("context", context_name)

    def export_tasks(self, report: str | None = None) -> list[Task]:
        command = ["rc.json.array=0", "rc.defaultheight=0"]
        context = self.get_context()
        if context and context.read_filter:
            command.extend(shlex.split(context.read_filter))
        command.append("export")
        if report:
            command.append(report)
        completed_process = self._run_task(*command)
        export = completed_process.stdout
        tasks = [Task.model_validate_json(t) for t in export.strip().split("\n")]
        log.debug(f"Got {len(tasks)} tasks from task_cli.")
        return tasks

    def get_config(self) -> Config:
        command = ["show"]
        config_output: str = self._run_task(*command).stdout.strip()
        return Config(config_output)

    def get_report_columns(self, report: str) -> list[tuple[str, str]]:
        command = ["show", "rc.defaultwidth=0", f"report.{report}.columns"]
        column_output: str = self._run_task(*command).stdout.strip()
        for line in column_output.split("\n"):
            if line.startswith(f"report.{report}.columns"):
                columns = line.split(" ")[1].split(",")
                break
        else:
            raise ValueError("Could not extract columns.")

        command = ["show", "rc.defaultwidth=0", f"report.{report}.labels"]
        label_output: str = self._run_task(*command).stdout.strip()
        for line in label_output.split("\n"):
            if line.startswith(f"report.{report}.labels"):
                labels = line.split(" ")[1].split(",")
                break
        else:
            raise ValueError("Could not extract labels.")

        return [(column, label) for column, label in zip(columns, labels)]

    def set_task_done(self, task: Task) -> None:
        log.info("Setting task %s to done", task.id)
        self._run_task(str(task.uuid), "done")

    def start_task(self, task: Task) -> None:
        log.info("Starting task %s", task.id)
        self._run_task(str(task.uuid), "start")

    def stop_task(self, task: Task) -> None:
        log.info("Stopping task %s", task.id)
        self._run_task(str(task.uuid), "stop")

    def modify_task(self, task: Task, modification: str) -> None:
        log.info("Modifying task %s", task.id)
        modification_args = modification.split(" ")
        completed_process = self._run_task(str(task.uuid), "modify", *modification_args)
        if completed_process.returncode != 0:
            log.error("Failed to modify task: %s", completed_process.stderr)
            raise ValueError(completed_process.stderr.strip())

    def annotate_task(self, task: Task, annotation: str) -> None:
        log.info("Annotating task %s", task.id)
        completed_process = self._run_task(str(task.uuid), "annotate", annotation)
        if completed_process.returncode != 0:
            log.error("Failed to annotate task %s: %s", task.id, completed_process)
            raise ValueError(completed_process.stderr.strip())

    def add_task(self, description: str) -> int:
        log.info("Adding task with description %s", description)
        # split so that description isn't passed as one complete string (which would not allow to add prio/proj/etc.)
        description: list[str] = description.split(" ")
        completed_process = self._run_task("add", *description)
        if completed_process.returncode != 0:
            log.error("Failed to create task: %s", completed_process)
            raise ValueError(completed_process.stderr.strip())

        confirmation = completed_process.stdout.strip()
        # TASKDATA override: ./test_data/
        # Created task 4.
        task_id_pattern = r"Created task (\d+)"
        match = re.search(task_id_pattern, confirmation)
        if match is None:
            log.error("Failed to get task id from new task")
            raise ValueError("Failed to get task id from new task")

        task_id = int(match.group(1))
        log.debug("Added new task with id %d", task_id)
        return task_id

    def log_task(self, description: str) -> None:
        log.info("Logging task with description %s", description)
        description_arguments: list[str] = description.split(" ")
        completed_process = self._run_task("log", *description_arguments)
        if completed_process.returncode != 0:
            log.error("Failed to log task: %s", completed_process)
            raise ValueError(completed_process.stderr.strip())

    def delete_task(self, task: Task) -> None:
        log.info("Deleting task %s", task.id)
        completed_process = self._run_task("rc.confirmation=off", "rc.recurrence.confirmation=no", str(task.id), "delete")
        if completed_process.returncode != 0:
            log.error("Failed to delete task: %s", completed_process)
            raise ValueError(completed_process.stderr.strip())

    def edit_task(self, task: Task) -> None:
        """Open the task in the user's $EDITOR via `task <uuid> edit`.

        Must be called while the TUI is suspended so the editor can take over the terminal.
        """
        log.info("Editing task %s", task.id)
        command = [self.base_command, str(task.uuid), "edit"]
        log.debug("Running `%s`", " ".join(command))
        completed_process = subprocess.run(command)
        if completed_process.returncode != 0:
            log.error("Failed to edit task %s (exit code %d)", task.id, completed_process.returncode)
            raise ValueError(f"task edit exited with code {completed_process.returncode}")
