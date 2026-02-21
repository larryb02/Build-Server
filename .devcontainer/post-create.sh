#!/usr/bin/env bash
set -euo pipefail

# # Install Terraform via HashiCorp APT repository
# sudo apt-get update
# sudo apt-get install -y gnupg software-properties-common
# wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
# echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
# sudo apt-get install -y terraform

# Install k3d
curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash

# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
rm kubectl

# Create k3d cluster with 2 agents
k3d cluster delete dev # need to do this because k3d clusters aren't being destroyed when the container is destroyed...
k3d cluster create dev --agents 2

# Install Ansible + dependencies
pip install -r .devcontainer/requirements.txt

# Install projects
pip install -e ./buildserver-api[test] -e ./buildserver-runner[test]

# Install dev tools
pip install pylint pre-commit
pre-commit install
