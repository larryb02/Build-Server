# Build-Server

[![CI](https://github.com/larryb02/Build-Server/actions/workflows/deploy.yaml/badge.svg)](https://github.com/larryb02/Build-Server/actions/workflows/deploy.yaml) [![Documentation](https://readthedocs.org/projects/build-server/badge/?version=latest)](https://build-server.readthedocs.io/)

A CI/CD system for building programs.

## Components

- **API** - REST API for submitting and managing build jobs
- **Runner** - Distributed execution nodes that consume and run jobs from the queue. Multiple runners can operate concurrently
- **Rebuilder** - Background task that polls registered repositories for new commits and triggers rebuilds
- **Database** - PostgreSQL for storing job and artifact metadata

## Quick Start

Clone the repository and open it in VS Code. When prompted, reopen in the dev container — it will automatically set up a local k3d cluster and install all dependencies.

Deploy all services to the cluster:

```bash
ansible-playbook infra/ansible/site.yml
```

Submit a job:

```bash
curl -X POST http://<cluster-ip>/jobs/register \
  -H "Content-Type: application/json" \
  -d '{"git_repository_url": "https://github.com/user/repo.git"}'
```

For full documentation see [build-server.readthedocs.io](https://build-server.readthedocs.io/).
