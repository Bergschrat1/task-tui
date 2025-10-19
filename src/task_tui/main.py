import logging

import typer

from task_tui.app import TaskTuiApp
from task_tui.task import TaskCli

typer_app = typer.Typer()
log = logging.getLogger(__name__)

DEFAULT_REPORT = "next"


@typer_app.command()
def health() -> None:
    try:
        log.debug("Initiating TaskCli")
        TaskCli()
    except Exception as e:
        log.error("Could not initiate TaskCli: %s", e, exc_info=e)
        raise e
    print("Everything seems to work fine!")


@typer_app.command()
def task_tui(report: str = DEFAULT_REPORT) -> None:
    log.debug("Starting TUI with report %s.", report)
    task_tui_app = TaskTuiApp()
    task_tui_app.report = report
    task_tui_app.run()


@typer_app.callback(invoke_without_command=True)
def main(ctx: typer.Context, verbose: bool = False) -> None:
    logging_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(format="%(asctime)s %(name)s %(levelname)s:%(message)s", level=logging_level, filename="./task-tui.log")
    log.debug("\nStarting application.")
    log.info("Logging Level is %s", logging_level)
    if ctx.invoked_subcommand is None:  # run default TUI if no command given
        ctx.invoke(task_tui)


if __name__ == "__main__":
    typer_app()
