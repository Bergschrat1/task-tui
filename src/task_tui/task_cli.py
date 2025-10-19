import logging
import re
import subprocess

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
        command = ["rc.json.array=0", "export"]
        if report:
            command.append(report)
        export: str = self._run_task(*command).stdout
        tasks = [Task.model_validate_json(t) for t in export.strip().split("\n")]
        return tasks

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

    def add_task(self, description: str) -> int:
        log.info("Adding task with description %s", description)
        confirmation = self._run_task("add", description).stdout.strip()
        # TASKDATA override: ./test_data/
        # Created task 4.
        task_id_pattern = r"Created task (\d+)\."
        match = re.search(task_id_pattern, confirmation)
        if match is None:
            raise ValueError("Could not extract task ID of newly created task.")
        task_id = int(match.group(1))
        return task_id
