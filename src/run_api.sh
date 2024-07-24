#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$SCRIPT_DIR"

MAIN_SCRIPT="api_service:app"

HOST="0.0.0.0"
PORT=8000
WORKERS=2
MODE="production"

load_env() {
  if [ -f "$PARENT_DIR/.venv/bin/activate" ]; then
    source "$PARENT_DIR/.venv/bin/activate"
  fi
  if [ -f "$PARENT_DIR/.env" ]; then
    source "$PARENT_DIR/.env"
  fi
}

run_server() {
  if ! command -v uvicorn &> /dev/null; then
    echo "uvicorn is not installed. Please install it using: pip install uvicorn"
    exit 1
  fi

  if [ "$MODE" = "development" ]; then
    export LOGFIRE_LEVEL="debug"
    uvicorn "$MAIN_SCRIPT" \
      --host "$HOST" \
      --port "$PORT" \
      --reload
  else
    export LOGFIRE_LEVEL="info"
    uvicorn "$MAIN_SCRIPT" \
      --host "$HOST" \
      --port "$PORT" \
      --workers "$WORKERS"
  fi
}

while [[ $# -gt 0 ]]; do
  case $1 in
    --dev)
      MODE="development"
      shift
      ;;
    --port)
      PORT="$2"
      shift 2
      ;;
    --workers)
      WORKERS="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

load_env
run_server
