from fastapi.exceptions import RequestValidationError


def validate(repo_url: str):
    if repo_url == "":
        raise RequestValidationError("Url may not be blank")
    if not repo_url.startswith("https://"):
        raise RequestValidationError("Url must be https protocol")
