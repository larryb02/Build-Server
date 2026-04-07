# Build-Server

[![CI](https://github.com/larryb02/Build-Server/actions/workflows/deploy.yaml/badge.svg)](https://github.com/larryb02/Build-Server/actions/workflows/deploy.yaml) [![Documentation](https://readthedocs.org/projects/build-server/badge/?version=latest)](https://build-server.readthedocs.io/)

A CI/CD system for building programs.

<!-- ## Components

- **API** - REST API for submitting and managing build jobs
- **Runner** - Distributed execution nodes that consume and run jobs from the queue. Multiple runners can operate concurrently
- **Rebuilder** - Background task that polls registered repositories for new commits and triggers rebuilds
- **Database** - PostgreSQL for storing job and artifact metadata -->

## Quick Start

Start a PostgreSQL container:

```bash
docker run -d --name buildserver-db \
  -e POSTGRES_PASSWORD=example \
  -e POSTGRES_DB=buildserver \
  postgres:latest
```

Start the API:

```bash
docker run -d --restart=unless-stopped \
  --name buildserver-api \
  --link buildserver-db \
  -p 8000:8000 \
  ghcr.io/larryb02/build-server/api:latest \
  --db-host buildserver-db --db-password example --db-name buildserver
```

Register a runner:

```bash
# Generate a registration token
curl -X POST http://<server>/api/v1/runners/token

# Register the runner
buildserver-runner register -n <name> -t <token> -u <server>

# Start the runner
buildserver-runner start
```

Submit a job:

```bash
<<<<<<< HEAD
curl -X POST <hostname>/api/v1/jobs \
=======
curl -X POST http://<server>/api/v1/jobs \
>>>>>>> main
  -H "Content-Type: application/json" \
  -d '{"git_repository_url": "https://github.com/user/repo.git"}'
```

## Development

Clone the repository and open it in VS Code. When prompted, reopen in the dev container.

For full documentation see [build-server.readthedocs.io](https://build-server.readthedocs.io/).
