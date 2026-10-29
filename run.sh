#!/usr/bin/env bash
# ./run.sh web | app | smoke | unit | ticket PR1-T13616 | all   [--company stagingbatleap] [extra runner args]
#   web     Playwright Test (web/tests) on QA_BROWSERS (default chromium; e.g. chromium,firefox)   extra args: playwright
#   app     pytest + Appium (tests/app); QA_APP_DRIVER=adb for plain adb                           extra args: pytest
#   smoke | ticket <KEY> | all   both suites - the app suite runs even when the web one fails; the exit code says if any did
#   unit    both frameworks' own tests (no portal, device or secrets)
set -euo pipefail
cd "$(dirname "$0")"
{ [ -x .venv/bin/pytest ] && [ -d node_modules/@playwright/test ]; } || { echo "run ./setup.sh first"; exit 2; }
# Node from .nvmrc, for this script only - the nvm default is never changed
if [ -s "${NVM_DIR:-$HOME/.nvm}/nvm.sh" ]; then . "${NVM_DIR:-$HOME/.nvm}/nvm.sh" >/dev/null; nvm use --silent >/dev/null; fi

target="${1:-all}"; shift || true
key=""
if [ "$target" = ticket ]; then key="${1:?usage: ./run.sh ticket <KEY>}"; shift; fi
args=()
while [ $# -gt 0 ]; do
  case "$1" in
    --company) export QA_COMPANY="$2"; shift 2 ;;
    --company=*) export QA_COMPANY="${1#*=}"; shift ;;
    *) args+=("$1"); shift ;;
  esac
done
projects=()
IFS=, read -ra browsers <<< "${QA_BROWSERS:-chromium}"
for b in "${browsers[@]}"; do projects+=(--project="$b"); done

web() { npx playwright test "${projects[@]}" --pass-with-no-tests "$@"; }
app() { local code=0; .venv/bin/pytest "$@" || code=$?; [ "$code" -eq 5 ] && code=0; return "$code"; }  # 5 = nothing selected

status=0
case "$target" in
  web) web ${args[@]+"${args[@]}"} ;;
  app) app -m app ${args[@]+"${args[@]}"} ;;
  unit) npx playwright test --project=unit || status=$?; app -m unit || status=$? ;;
  smoke) web --grep @smoke || status=$?; app -m "app and smoke" || status=$? ;;
  ticket) web --grep "@$key\\b" || status=$?; app -m app --ticket "$key" || status=$? ;;
  all) web || status=$?; app -m "app or unit" || status=$? ;;
  *) echo "unknown target: $target (web | app | smoke | unit | ticket <KEY> | all)"; exit 2 ;;
esac
exit "$status"
