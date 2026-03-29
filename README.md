# Build-Server

[![CI](https://github.com/larryb02/Build-Server/actions/workflows/deploy.yaml/badge.svg)](https://github.com/larryb02/Build-Server/actions/workflows/deploy.yaml) [![Documentation](https://readthedocs.org/projects/build-server/badge/?version=latest)](https://build-server.readthedocs.io/)

A CI/CD system for building programs.

## Components

- **API** - Control plane
- **Runner** - Distributed execution nodes
- **Database** - PostgreSQL

## Quick Start

Deploy API to cluster:

```bash
ansible-playbook infra/ansible/site.yml
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
curl -X POST http://<server>/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{"git_repository_url": "https://github.com/user/repo.git"}'
```

## Development

Clone the repository and open it in VS Code. When prompted, reopen in the dev container.

For full documentation see [build-server.readthedocs.io](https://build-server.readthedocs.io/).
