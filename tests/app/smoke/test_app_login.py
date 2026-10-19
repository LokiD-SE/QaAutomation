"""Smoke: the app opens, the default app user logs in and reaches a screen with the drawer."""

from __future__ import annotations

import pytest

from screens.app.home import MENU

pytestmark = [pytest.mark.app, pytest.mark.smoke]


def test_default_user_logs_in_and_sees_the_home_screen(app, evidence):
    evidence.app(app, "home")
    assert not app.has("Username"), "still on the login screen"
    assert any(app.find(name) for name in MENU), f"no drawer button; screen shows {app.texts()[:15]}"
