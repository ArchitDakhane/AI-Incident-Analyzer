#!/bin/sh
set -eu

mkdir -p "${UPLOAD_DIRECTORY:-/app/uploads/logs}" /app/logs
chown -R appuser:appuser "${UPLOAD_DIRECTORY:-/app/uploads/logs}" /app/logs
exec gosu appuser "$@"
