from importlib.metadata import version

__version__ = version("buildserver-runner")


def get_version():
    return __version__
