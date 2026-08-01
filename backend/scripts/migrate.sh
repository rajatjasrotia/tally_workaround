#!/usr/bin/env bash
set -e
# migrate.sh - Run Alembic migrations for this project
# Usage: ./migrate.sh [DATABASE_URL]
# If DATABASE_URL not provided, defaults to sqlite:///./backend/database.db

DB_URL=${1:-${DATABASE_URL:-sqlite:///./backend/database.db}}
export DATABASE_URL="$DB_URL"

# Ensure PYTHONPATH includes backend so alembic can import app.models
if [ -z "$PYTHONPATH" ]; then
  export PYTHONPATH="backend"
else
  export PYTHONPATH="$PYTHONPATH:backend"
fi

echo "Using DATABASE_URL=$DATABASE_URL"

# Activate backend venv if present
if [ -f "./backend/.venv/bin/activate" ]; then
  echo "Activating venv ./backend/.venv"
  # shellcheck disable=SC1091
  source ./backend/.venv/bin/activate
fi

# Run alembic upgrade
python -m alembic upgrade head
