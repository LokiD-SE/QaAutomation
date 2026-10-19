#!/usr/bin/env bash
# ./run.sh web | app | smoke | unit | ticket PR1-T13616 | all   [extra pytest args, e.g. --company stagingbatleap -x]
set -euo pipefail
cd "$(dirname "$0")"
[ -x .venv/bin/pytest ] || { echo "run ./setup.sh first"; exit 2; }
target="${1:-all}"; shift || true
case "$target" in
  web|app|smoke|unit|regression) exec .venv/bin/pytest -m "$target" "$@" ;;
  ticket) key="$1"; shift; exec .venv/bin/pytest --ticket "$key" "$@" ;;
  all) exec .venv/bin/pytest "$@" ;;
  *) exec .venv/bin/pytest "$target" "$@" ;;
esac
