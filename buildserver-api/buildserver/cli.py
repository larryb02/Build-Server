"""CLI entrypoint for the Build Server"""

import os

import typer
import uvicorn

from . import __version__

app = typer.Typer(no_args_is_help=True, help="Build Server")


@app.command(name="start")
def start(
    port: int = typer.Option(8000, "--port", "-p", help="Port to listen on"),
    db_host: str = typer.Option("postgres", "--db-host", help="Database hostname"),
    db_port: int = typer.Option(5432, "--db-port", help="Database port"),
    db_user: str = typer.Option("postgres", "--db-user", help="Database user"),
    db_password: str = typer.Option(
        "example", "--db-password", help="Database password"
    ),
    db_name: str = typer.Option("buildserver", "--db-name", help="Database name"),
    host: str = typer.Option("0.0.0.0", "--host", help="Host interface to bind"),
):
    """Start the Build Server API."""

    # TODO: env vars must be set before importing any buildserver modules so dynaconf
    # and database/core.py (which creates the engine at module scope) pick up the
    # correct values on first import. A factory pattern is ideal here, but will need to
    # fix some scope issues
    os.environ["BS_DATABASE_HOSTNAME"] = db_host
    os.environ["BS_DATABASE_PORT"] = str(db_port)
    os.environ["BS_DATABASE_USER"] = db_user
    os.environ["BS_DATABASE_PASSWORD"] = db_password
    os.environ["BS_DATABASE_NAME"] = db_name

    from .database.core import init_db
    from .main import app as fastapi_app
    from .utils import setup_logging

    setup_logging()
    init_db()
    uvicorn.run(fastapi_app, host=host, port=port, log_config=None)


def version_callback(value: bool):
    if value:
        typer.echo(f"Build Server v{__version__}")
        raise typer.Exit()


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
    """"""
