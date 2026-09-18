#!/bin/sh
# Container start-up for a hosted deployment.
#
# Migrations run before the server accepts traffic, so a deploy can never serve
# requests against a schema it does not expect. The port comes from the host
# (Render, Fly and Railway all inject PORT) and falls back to the local default.
#
# docker-compose and the laptop keep using the Dockerfile's own CMD; this script
# is only referenced by render.yaml.
set -e

alembic upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
