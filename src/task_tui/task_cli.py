import logging
import re
import subprocess

from task_tui.config import Config
from task_tui.data_models import Task

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

    def export_tasks(self, report: str | None = None) -> list[Task]:
        command = ["rc.json.array=0", "rc.defaultheight=0", "export"]
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
        task_id_pattern = r"Created task (\d+)\."
        match = re.search(task_id_pattern, confirmation)
        if match is None:
            log.error("Failed to get task id from new task")
            raise ValueError("Failed to get task id from new task")

        task_id = int(match.group(1))
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
        completed_process = self._run_task(str(task.id), "delete")
        if completed_process.returncode != 0:
            log.error("Failed to delete task: %s", completed_process)
            raise ValueError(completed_process.stderr.strip())
