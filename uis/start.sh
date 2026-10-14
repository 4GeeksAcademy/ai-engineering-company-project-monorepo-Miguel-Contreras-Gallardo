#!/bin/sh
# TrackFlow UIs — Start script
# Arranca website en :3000 y backoffice en :3001

set -e

echo "==> Starting TrackFlow website on :3000"
cd /app/website && serve . -p 3000 --single &
PID_WEBSITE=$!

echo "==> Starting TrackFlow backoffice on :3001"
cd /app/backoffice && serve . -p 3001 --single &
PID_BACKOFFICE=$!

# Forward signals to child processes
trap "kill $PID_WEBSITE $PID_BACKOFFICE 2>/dev/null; exit 0" SIGTERM SIGINT

echo "==> TrackFlow UIs running: website (:3000), backoffice (:3001)"
wait