import logging

import typer

from runner.config import LOG_LEVEL
from runner.agent import Agent

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)


def version_callback(value: bool):
    if value:
        print("buildserver-runner 0.1.0")
        raise typer.Exit()


app = typer.Typer(no_args_is_help=True)


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
):
    """Buildserver Runner - execution node for buildserver"""


@app.command(name="start", help="Start buildserver-runner")
def start_runner():
    Agent().start()


if __name__ == "__main__":
    app()
