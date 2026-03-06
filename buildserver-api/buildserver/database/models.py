"""Import all ORM models to ensure they're registered on Base before create_all."""

import buildserver.api.jobs.models  # noqa: F401
import buildserver.api.runners.models  # noqa: F401
import buildserver.api.auth.models  # noqa: F401
