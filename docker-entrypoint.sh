#!/bin/bash
set -e

echo "Running Migrations"
# Run migrations
alembic upgrade head

echo "Starting application .. .. "
poetry run uvicorn app.main:app --host 0.0.0.0 --port 80