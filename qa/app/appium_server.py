"""The Appium server for app tests: the one at QA_APPIUM_URL when it answers, else one this run starts from the repo's
own install (node_modules/.bin/appium, driver uiautomator2 - `./setup.sh` installs both) and stops at the end.

Appium needs Node >= 20.19 (the repo's .nvmrc: 24) and an Android SDK: ANDROID_HOME when it holds platform-tools,
else ~/Android/Sdk, else ANDROID_SDK_ROOT. The server's log goes to reports/appium.log.
"""

from __future__ import annotations

import os
import re
import subprocess
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from qa.config import ROOT

APPIUM_BIN = ROOT / "node_modules" / "appium" / "index.js"
LOG = ROOT / "reports" / "appium.log"
START_TIMEOUT_S = 90


class AppiumServerError(RuntimeError):
    pass


def is_up(url: str) -> bool:
    try:
        with urllib.request.urlopen(url.rstrip("/") + "/status", timeout=3) as response:
            return response.status == 200
    except OSError:
        return False


def node_binary() -> str:
    """QA_NODE, else the nvm install matching .nvmrc, else `node` on PATH (run.sh puts the right one there)."""
    if os.environ.get("QA_NODE"):
        return os.environ["QA_NODE"]
    wanted = (ROOT / ".nvmrc").read_text().strip() if (ROOT / ".nvmrc").is_file() else ""
    nvm = Path(os.environ.get("NVM_DIR", Path.home() / ".nvm")) / "versions" / "node"
    if wanted and nvm.is_dir():
        found = sorted(nvm.glob(f"v{wanted}.*/bin/node"), key=lambda p: [int(n) for n in re.findall(r"\d+", p.parts[-3])])
        if found:
            return str(found[-1])
    return "node"


def android_home() -> str:
    candidates = [os.environ.get("ANDROID_HOME", ""), str(Path.home() / "Android" / "Sdk"), os.environ.get("ANDROID_SDK_ROOT", "")]
    return next((c for c in candidates if c and (Path(c) / "platform-tools" / "adb").exists()), "")


class AppiumServer:
    def __init__(self, process: subprocess.Popen, log):
        self.process, self._log = process, log

    def stop(self) -> None:
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self._log.close()


def ensure_server(url: str) -> AppiumServer | None:
    """None when a server already answers at `url` (it is left running); else the server this call started."""
    if is_up(url):
        return None
    parsed = urlparse(url)
    if parsed.hostname not in ("127.0.0.1", "localhost"):
        raise AppiumServerError(f"no Appium server answers at {url}")
    if not APPIUM_BIN.is_file():
        raise AppiumServerError("Appium is not installed in this repo: run ./setup.sh (npm ci + appium driver install)")
    env = dict(os.environ)
    sdk = android_home()
    if sdk:
        env["ANDROID_HOME"] = env["ANDROID_SDK_ROOT"] = sdk
    LOG.parent.mkdir(parents=True, exist_ok=True)
    log = open(LOG, "a", encoding="utf-8")  # noqa: SIM115 - closed by AppiumServer.stop
    process = subprocess.Popen([node_binary(), str(APPIUM_BIN), "--address", parsed.hostname, "--port", str(parsed.port or 4723),
                                "--log-level", "warn", "--log-no-colors"], cwd=ROOT, env=env, stdout=log,
                               stderr=subprocess.STDOUT)
    server = AppiumServer(process, log)
    deadline = time.monotonic() + START_TIMEOUT_S
    while time.monotonic() < deadline:
        if is_up(url):
            return server
        if process.poll() is not None:
            break
        time.sleep(1)
    server.stop()
    tail = LOG.read_text(encoding="utf-8", errors="replace").strip().splitlines()[-3:]
    raise AppiumServerError(f"Appium did not start at {url}: {' | '.join(tail) or 'no output'} (log: {LOG})")
