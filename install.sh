#!/usr/bin/env bash
set -e

echo "Setting up otto-factory..."

# Python check
if ! command -v python3 &>/dev/null; then
    echo "Error: python3 not found. Install Python 3.10+ from https://www.python.org/downloads/"
    exit 1
fi

# Virtual environment
python3 -m venv venv
echo "Virtual environment created."

# Dependencies
venv/bin/pip install --quiet -r requirements.txt
echo "Dependencies installed."

# Config file
if [ -f .env ]; then
    echo ".env already exists — leaving it unchanged."
else
    cp .env.example .env
    echo "Created .env from template."
fi

echo ""
echo "Setup complete. To start using otto-factory:"
echo ""
echo "  source venv/bin/activate"
echo ""
echo "Then follow the README to configure your first project."
