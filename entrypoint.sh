#!/bin/sh
set -e

echo "Waiting for database and applying migrations..."
alembic upgrade head

echo "Starting API..."
exec "$@"
