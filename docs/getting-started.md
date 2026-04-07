# Getting Started

## Running with Docker

The quickest way to run Build Server is with Docker.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)

### Start the API

```bash
docker run -d --restart=unless-stopped \
  --name buildserver-api \
  --link buildserver-db \
  -p 8000:8000 \
  ghcr.io/larryb02/build-server/api:latest \
  --db-host buildserver-db --db-password example --db-name buildserver
```

All database options can also be provided via environment variables:

| Flag | Env var | Default |
|---|---|---|
| `--db-host` | `BS_DATABASE_HOSTNAME` | `postgres` |
| `--db-port` | `BS_DATABASE_PORT` | `5432` |
| `--db-user` | `BS_DATABASE_USER` | `postgres` |
| `--db-password` | `BS_DATABASE_PASSWORD` | `example` |
| `--db-name` | `BS_DATABASE_NAME` | `buildserver` |

### Submitting a Job

With the cluster running, submit a repository for building via the API:

```bash
curl -X POST https://<hostname>/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{"git_repository_url": "https://github.com/user/repo.git"}'
```
