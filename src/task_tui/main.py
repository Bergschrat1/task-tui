import logging

import typer

from task_tui.app import TaskStore, TaskTuiApp
from task_tui.task import TaskCli

typer_app = typer.Typer()
log = logging.getLogger(__name__)

DEFAULT_REPORT = "next"


@typer_app.command()
def health():
    try:
        log.debug("Initiating TaskCli")
        TaskCli()
    except Exception as e:
        log.error("Could not initiate TaskCli: %s", e, exc_info=e)
        raise e
    print("Everything seems to work fine!")


@typer_app.command()
def task_tui(report: str = DEFAULT_REPORT):
    task_cli = TaskCli()
    tasks = task_cli.export_tasks(report)
    headings = task_cli.get_report_columns(report)
    task_tui_app = TaskTuiApp()
    task_tui_app.tasks = TaskStore(tasks)
    task_tui_app.headings = headings
    task_tui_app.run()



@typer_app.callback(invoke_without_command=True)
def main(ctx: typer.Context, verbose: bool = False):
    logging_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(format="%(asctime)s %(name)s %(levelname)s:%(message)s", level=logging_level)
    log.info("Logging Level is %s", logging_level)
    if ctx.invoked_subcommand is None:  # run default TUI if no command given
        ctx.invoke(task_tui)


if __name__ == "__main__":
    typer_app()
