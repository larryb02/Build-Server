#!/usr/bin/env bash
set -euo pipefail

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install projects (editable)
pip install -e ./buildserver-api[test] -e ./buildserver-runner[test]

# Install dev tools
pip install pylint pre-commit
pre-commit install
