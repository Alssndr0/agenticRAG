#!/bin/sh

export APP_MODULE=${APP_MODULE-app.main:app}
export HOST=${HOST:-0.0.0.0}
export PORT=${AIMW_PORT:-8000}

# run uvicorn
exec uvicorn --reload --host $HOST --port $PORT "$APP_MODULE"
# exec uvicorn $APP_MODULE.main:app --host $HOST --port $PORT --reload --log-level debug