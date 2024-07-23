#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"

MAIN_SCRIPT="$SCRIPT_DIR/bot_service.py"

run_bot() {
  python3 "$MAIN_SCRIPT"
}

load_venv() {
  if [ -f "$PARENT_DIR/.venv/bin/activate" ]; then
    source "$PARENT_DIR/.venv/bin/activate"
  fi
}

run_bot_with_reload() {
  if ! command -v watchmedo &> /dev/null; then
    echo "watchmedo is not installed. Please install it using: pip install watchmedo"
    exit 1
  fi
  watchmedo auto-restart \
    --directory="$SCRIPT_DIR" \
    --pattern="*.py" \
    --recursive \
    -- python3 "$MAIN_SCRIPT"
}

load_venv

if [ "$1" == "--dev" ]; then
  run_bot_with_reload
else
  run_bot
fi
