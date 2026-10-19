"""Portal login, done once per role and company and reused through Playwright's storage state."""

from __future__ import annotations

import hashlib
import time
from pathlib import Path

from playwright.sync_api import Browser, Page

from qa.config import ROOT, Login

LOGIN_PATH = "/users/login"
USERNAME = '#UserUsername, input[name="data[User][username]"], input[name="User[username]"]'
PASSWORD = '#password, input[name="data[User][password]"], input[name="User[password]"]'
SUBMIT = "#loginBtn"
LOGIN_TIMEOUT_MS = 40_000
STATE_DIR = ROOT / "reports" / ".auth"
STATE_MAX_AGE_S = 6 * 3600  # a portal session outlives a test run; older states are refreshed


class LoginError(AssertionError):
    pass


def login(page: Page, base_url: str, who: Login) -> None:
    """Sign in on `page`. The portal leaves /users/login on success and re-renders it on failure, so the URL is the
    signal; the landing page can hang on slow resources, so only DOM content is waited for."""
    page.goto(base_url + LOGIN_PATH, wait_until="domcontentloaded")
    page.fill(USERNAME, who.user)
    page.fill(PASSWORD, who.password)
    page.click(SUBMIT)
    try:
        page.wait_for_url(lambda url: LOGIN_PATH not in url, timeout=LOGIN_TIMEOUT_MS, wait_until="domcontentloaded")
    except Exception as exc:  # noqa: BLE001 - Playwright's own timeout type
        raise LoginError(f"login as {who.user} did not leave {LOGIN_PATH} (still at {page.url})") from exc
    if not page.url.startswith(base_url):  # some roles land on a page the browser cannot render
        page.goto(base_url + "/users/dashboard", wait_until="domcontentloaded")


def state_file(base_url: str, who: Login) -> Path:
    key = hashlib.sha1(f"{base_url}|{who.user}".encode()).hexdigest()[:12]
    return STATE_DIR / f"{key}.json"


def auth_state(browser: Browser, base_url: str, who: Login, context_args: dict | None = None) -> Path:
    """A storage-state file for `who` on `base_url`, logged in once and reused until it is STATE_MAX_AGE_S old."""
    path = state_file(base_url, who)
    if path.is_file() and time.time() - path.stat().st_mtime < STATE_MAX_AGE_S:
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    context = browser.new_context(**(context_args or {}))
    try:
        login(context.new_page(), base_url, who)
        context.storage_state(path=str(path))
    finally:
        context.close()
    return path
