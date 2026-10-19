"""Settings from the environment and `.env` - the same variable names Greybox uses, so one .env can serve both.

    BIZOM_WEB_URL / BIZOM_WEB_USER / BIZOM_WEB_PASSWORD     default company
    BIZOM_WEB_ROLE_<ROLE>=user/password                       a login per role (spaces as underscores; n/a = none)
    BIZOM_APP_USER / BIZOM_APP_PASSWORD, BIZOM_APP_ROLE_<ROLE>
    <any of the above>_<COMPANY>                              per-company values, picked with --company / QA_COMPANY

Secrets live only in `.env` (gitignored) or CI secrets - never in the code or the test data.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOT_APPLICABLE = "n/a"


class ConfigError(RuntimeError):
    """A setting the test needs is missing - reported as a skip, never as a product failure."""


def load_dotenv(path: Path | None = None) -> None:
    """KEY=value lines into os.environ; values already set win (CI secrets, the shell)."""
    path = path or ROOT / ".env"
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@dataclass
class Login:
    user: str
    password: str


@dataclass
class Settings:
    company: str = ""
    web_url: str = ""
    web_user: str = ""
    web_password: str = ""
    app_user: str = ""
    app_password: str = ""
    app_package: str = "co.bizom.apps"
    device_serial: str = ""
    headless: bool = True
    extra: dict = field(default_factory=dict)

    def _env(self, key: str) -> str:
        """`key` for this company (KEY_<COMPANY>), else the default one."""
        if self.company:
            value = os.environ.get(f"{key}_{self.company.upper()}")
            if value is not None:
                return value.strip()
        return (os.environ.get(key) or "").strip()

    def web_login(self, role: str = "") -> Login:
        return self._login("WEB", role, self.web_user, self.web_password)

    def app_login(self, role: str = "") -> Login:
        return self._login("APP", role, self.app_user, self.app_password)

    def _login(self, surface: str, role: str, user: str, password: str) -> Login:
        if role:
            raw = self._env(f"BIZOM_{surface}_ROLE_{role.upper().replace(' ', '_')}")
            if raw.lower() == NOT_APPLICABLE:
                raise ConfigError(f"{surface.lower()} role {role} has no login on {self.company or 'this company'} (n/a)")
            name, _, secret = raw.partition("/")
            if name and secret:
                return Login(name, secret)
            if role.upper() not in ("ADMIN", "DEFAULT"):
                raise ConfigError(f"no {surface.lower()} login for role {role}: set BIZOM_{surface}_ROLE_"
                                  f"{role.upper().replace(' ', '_')}=user/password in .env")
        if not (user and password):
            raise ConfigError(f"no default {surface.lower()} login: set BIZOM_{surface}_USER / _PASSWORD in .env")
        return Login(user, password)


def settings(company: str | None = None) -> Settings:
    load_dotenv()
    company = (company if company is not None else os.environ.get("QA_COMPANY", "")).strip().lower()
    s = Settings(company=company)
    s.web_url = s._env("BIZOM_WEB_URL").rstrip("/")
    s.web_user, s.web_password = s._env("BIZOM_WEB_USER"), s._env("BIZOM_WEB_PASSWORD")
    s.app_user, s.app_password = s._env("BIZOM_APP_USER"), s._env("BIZOM_APP_PASSWORD")
    s.app_package = s._env("BIZOM_APP_PACKAGE") or s.app_package
    s.device_serial = s._env("QA_DEVICE") or s._env("ANDROID_SERIAL")
    if not s.company and s.web_url:  # https://stagingbatleap.bizomstaging.in -> stagingbatleap (picks the test data)
        s.company = re.sub(r"^https?://", "", s.web_url).split(".")[0].lower()
    s.headless = (os.environ.get("QA_HEADED", "") or "0") in ("0", "", "false")
    return s
