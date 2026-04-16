#!/usr/bin/env bash
set -euo pipefail

# Create virtual environment
python -m venv .venv && .venv/bin/pip install -r .devcontainer/requirements.dev.txt

# Install projects (editable)
.venv/bin/pip install -e ./buildserver-api[test] -e ./buildserver-runner[test]

# pre-commit install
