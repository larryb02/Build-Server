import logging

# import grpc
import httpx
import typer

# from protos import registry_pb2, registry_pb2_grpc

from runner.config import LOG_LEVEL, CONFIG_PATH, create_runner_config
from runner.agent import Agent

logging.basicConfig(level=LOG_LEVEL, force=True)
logger = logging.getLogger(__name__)


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
    try:
        Agent().start()
    except RuntimeError as exc:
        logger.error(exc)
        print("No runner registered.")


@app.command(name="register", help="register runner to server")
def register(
    name: str = typer.Option(None, "--name", "-n", help="Runner name"),
    token: str = typer.Option(..., "--token", "-t", help="Registration token"),
    url: str = typer.Option(..., "--url", "-u", help="Buildserver API URL"),
):
    # TODO: Add interactive prompts
    try:
        # TODO: check status codes and/or create custom statuses to improve UX
        r = httpx.post(
            url=f"{url}/api/v1/runners/",
            headers={"Content-Type": "application/json"},
            json={"token": token, "name": name},
            follow_redirects=True,
        )
        r.raise_for_status()
        create_runner_config(token=token, name=name, api_url=url)
    except httpx.HTTPError as exc:
        logger.debug(exc)
        print("Failed to register runner: %s", exc)


if __name__ == "__main__":
    app()
