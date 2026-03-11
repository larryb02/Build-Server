import logging

import grpc
import typer
from protos import registry_pb2, registry_pb2_grpc

from runner.config import LOG_LEVEL, CONFIG_PATH, create_runner_config
from runner.agent import Agent

logging.basicConfig()
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
    channel = grpc.insecure_channel(f"{url}")
    registry = registry_pb2_grpc.RegistryStub(channel)
    try:
        response = registry.Register(
            registry_pb2.RegisterRequest(name=name, token=token)
        )
        # write response to a toml file
        create_runner_config(
            token=response.runner.token, name=response.runner.name, api_url=url
        )
        logger.info("config written to %s", CONFIG_PATH)
    except grpc.RpcError as exc:
        # TODO: check status codes and/or create custom statuses to improve UX
        logger.error(exc)
        print("Failed to register runner")


if __name__ == "__main__":
    app()
