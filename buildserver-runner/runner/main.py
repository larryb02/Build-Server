import logging

import typer

from runner.config import LOG_LEVEL

# import Agent
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)

app = typer.Typer(no_args_is_help=True)


@app.command()
def main(version: bool = typer.Option(None, "--version", "-v")):
    print(LOG_LEVEL)


@app.command(name="start", help="start buildserver-runner")
def start_runner():
    pass


if __name__ == "__main__":
    app()
