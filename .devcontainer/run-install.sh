#!/bin/bash

# Install project dependencies (always required)
echo 'Installing project dependencies...'
pip install -e ".[dev]"

# Install optional dev tools (only in local environment)
if [ "$CI" != "true" ] && [ -f .devcontainer/install-dev-tools.sh ]; then
  echo 'Local environment & custom script detected. Executing script...';
  bash .devcontainer/install-dev-tools.sh;
else
  echo 'Skipping optional dev tools (CI environment or script missing).'
fi

