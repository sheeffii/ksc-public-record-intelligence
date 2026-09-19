#!/usr/bin/env sh
# Apply migrations and seed public case metadata before serving.
# Both steps are idempotent. Nothing is downloaded.
set -eu

if [ "${SKIP_MIGRATIONS:-0}" != "1" ]; then
  echo "[entrypoint] alembic upgrade head"
  alembic upgrade head
  echo "[entrypoint] seeding case metadata"
  ksc-seed
fi

exec "$@"
