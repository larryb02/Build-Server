import logging
from pathlib import Path

import toml
from dynaconf import Dynaconf

CONFIG_PATH = Path(Path.home() / ".bs" / "config.toml")

settings = Dynaconf(envvar_prefix="BS", settings_files=[CONFIG_PATH])

LOG_LEVEL = settings.get("LOG_LEVEL", logging.INFO)
APISERVER_HOST = settings.get("RUNNERS.API_URL", None)
RUNNER_TOKEN = settings.get("RUNNERS.TOKEN", None)


def create_runner_config(token, name, api_url):
    """Write runner config to config.toml."""
    if not CONFIG_PATH.exists():
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.touch()
    config = {"runners": {"api_url": api_url, "name": name, "token": token}}
    with open(CONFIG_PATH, mode="w", encoding="utf-8") as f:
        toml.dump(config, f)
