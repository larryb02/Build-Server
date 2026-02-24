# Getting Started

## Running Locally with k3d

k3d is used to run a lightweight Kubernetes cluster locally inside Docker. This allows you to deploy and test the full Build Server stack on your machine without any cloud infrastructure.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [VS Code](https://code.visualstudio.com/) with the [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension

## Setup

Clone the repository and open it in VS Code. When prompted, reopen in the dev container. The container will automatically:

- Install `k3d` and `kubectl`
- Create a local k3d cluster (`dev`) with 2 agent nodes
- Install Ansible and its dependencies (`ansible`, `kubernetes`, `PyYAML`, `jsonpatch`, `ansible-dev-tools`)
- Install buildserver-api and buildserver-runner packages

If you prefer not to use the dev container, install the above dependencies manually.

### Deploying to the Cluster

Once inside the dev container, deploy all services to the local k3d cluster using Ansible:

```bash
ansible-playbook infra/ansible/site.yml
```

!!! note
    To remove application from the cluster run `ansible-playbook infra/ansible/site.yml -e "k8s_state=absent"`

This deploys the following into the `buildserver` namespace:

- PostgreSQL
- RabbitMQ
- buildserver-api
- buildserver-runner

### Submitting a Job

With the cluster running, submit a repository for building via the API:

```bash
curl -X POST http://<cluster-ip>/jobs/register \
  -H "Content-Type: application/json" \
  -d '{"git_repository_url": "https://github.com/user/repo.git"}'
```

!!! warning
    All builds will currently fail as `make` is not installed in the runner container. User-defined script execution is the next planned feature.
