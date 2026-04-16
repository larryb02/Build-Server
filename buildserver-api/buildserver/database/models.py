"""Import all ORM models to ensure they're registered on Base before create_all."""

import buildserver.api.pipelines.models  # noqa: F401
import buildserver.api.runners.models  # noqa: F401
import buildserver.api.auth.models  # noqa: F401
import buildserver.api.projects.models  # noqa: F401
