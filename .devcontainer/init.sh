#! /bin/bash
python3 -m venv init.venv
source init.venv/bin/activate
python3 -m pip install -r requirements.txt
ansible-playbook infra/ansible/deploy_buildserver/site.yml --tags dev -e cluster_namespace=devpod
deactivate
