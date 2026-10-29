#!/usr/bin/env bash
# One-time setup, all inside this repo:
#   Node (.nvmrc, via nvm - the nvm default is never changed), Playwright Test + Chromium, Appium + its UiAutomator2
#   driver (node_modules), the app suite's own virtualenv (never Greybox's), and the .env.
set -euo pipefail
cd "$(dirname "$0")"

NVM_SH="${NVM_DIR:-$HOME/.nvm}/nvm.sh"
if [ -s "$NVM_SH" ]; then
  . "$NVM_SH" >/dev/null
  nvm install >/dev/null   # the version in .nvmrc, for this shell only
  nvm use --silent >/dev/null
fi
node -e 'process.exit(+process.versions.node.split(".")[0] >= 24 ? 0 : 1)' \
  || { echo "Node 24 needed (.nvmrc): install nvm (https://github.com/nvm-sh/nvm) or Node 24, then re-run"; exit 2; }
npm ci --no-fund --no-audit
npx playwright install chromium            # QA_BROWSERS=chromium,firefox,webkit needs those too
npx appium driver list --installed 2>&1 | grep -q uiautomator2 || npx appium driver install uiautomator2

python3 -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -e ".[dev]"

if [ ! -e .env ]; then
  GREYBOX_ENV="${GREYBOX_HOME:-$HOME/Workspace/greybox-mobithon-2026}/.env"
  if [ -f "$GREYBOX_ENV" ]; then
    read -r -p "Link Greybox's .env ($GREYBOX_ENV) instead of copying secrets? [Y/n] " answer
    if [ "${answer:-y}" != "n" ]; then ln -s "$GREYBOX_ENV" .env; echo "linked .env -> $GREYBOX_ENV"; fi
  fi
  [ -e .env ] || { cp .env.example .env; echo "wrote .env from .env.example - fill in the logins"; }
fi

[ -n "${ANDROID_HOME:-}" ] || [ -x "$HOME/Android/Sdk/platform-tools/adb" ] \
  || echo "note: app tests need an Android SDK - set ANDROID_HOME (Appium uses its platform-tools / build-tools)"
./run.sh unit
