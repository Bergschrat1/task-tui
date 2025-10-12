import typer
import logging
import subprocess

typer_app = typer.Typer()
log = logging.getLogger(__name__)

class TaskCli:
    base_command: str = "task"

    def __init__(self) -> None:
        try:
            self.run_task("show")
        except FileNotFoundError:
            raise FileNotFoundError("The task CLI tool doesn't seem to be installed.")
        except Exception:
            raise Exception("Could not run `task show`")

    def run_task(self, *args: str, **kwargs) -> subprocess.CompletedProcess:
        command = [self.base_command, *args]
        log.debug("Running `%s`", " ".join(command))
        return subprocess.run(command, capture_output=True, **kwargs)

@typer_app.command()
def health():
    try:
        log.debug("Initiating TaskCli")
        TaskCli()
    except Exception as e:
        log.error("Could not initiate TaskCli: %s", e, exc_info=e)
        raise e
    print("Everything seems to work fine!")


@typer_app.callback()
def main(verbose: bool = False):
    logging_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        format="%(asctime)s %(name)s %(levelname)s:%(message)s", level=logging_level
    )

if __name__ == "__main__":
    typer_app()
