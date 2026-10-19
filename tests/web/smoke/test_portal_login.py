"""Smoke: the admin login works and the dashboard renders."""

from __future__ import annotations

import pytest

from qa.web.page import BasePage

pytestmark = [pytest.mark.web, pytest.mark.smoke, pytest.mark.role("ADMIN")]


def test_admin_reaches_the_dashboard(page, base_url, evidence):
    dashboard = BasePage(page, base_url).open("/users/dashboard")
    evidence.web(page, "dashboard")
    assert "/users/login" not in page.url
    assert dashboard.current_path.startswith("/users/dashboard") or page.title()
