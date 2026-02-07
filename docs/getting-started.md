# Getting Started

## Requirements

- Python 3.12+
- PostgreSQL
- RabbitMQ

## Environment Variables

Store this `.env` in `/buildserver`:

```
DATABASE_PORT=
DATABASE_HOSTNAME=
DATABASE_USER=
DATABASE_PASSWORD=
DATABASE_NAME=

LOG_LEVEL=DEBUG

RABBITMQ_HOST=
RABBITMQ_PORT=
RABBITMQ_USER=
RABBITMQ_PASSWORD=

ARTIFACT_REPOSITORY_ROOT=
```

## Installation

Clone repository:

```bash
git clone git@github.com:larryb02/Build-Server.git
```

Setup a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install package:

```bash
pip install -e .
```

## Running the API

```bash
buildserver
```

## Running the Agent

```bash
buildserver-agent
```

## Kicking Off Builds

To register repositories for builds, use the REST API:

```bash
curl -X POST http://localhost:8000/jobs/register \
  -H "Content-Type: application/json" \
  -d '{"git_repository_url": "git@github.com:user/repo.git"}'
```
