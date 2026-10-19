#!/usr/bin/env bash
# One-time setup: the suite's own virtualenv (never Greybox's), Chromium for Playwright, and the .env.
set -euo pipefail
cd "$(dirname "$0")"
python3 -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -e ".[dev]"
.venv/bin/playwright install chromium
if [ ! -e .env ]; then
  GREYBOX_ENV="${GREYBOX_HOME:-$HOME/Workspace/greybox-mobithon-2026}/.env"
  if [ -f "$GREYBOX_ENV" ]; then
    read -r -p "Link Greybox's .env ($GREYBOX_ENV) instead of copying secrets? [Y/n] " answer
    if [ "${answer:-y}" != "n" ]; then ln -s "$GREYBOX_ENV" .env; echo "linked .env -> $GREYBOX_ENV"; fi
  fi
  [ -e .env ] || { cp .env.example .env; echo "wrote .env from .env.example - fill in the logins"; }
fi
.venv/bin/pytest tests/unit -q
