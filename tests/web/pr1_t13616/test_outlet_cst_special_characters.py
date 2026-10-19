"""PR1-T13616 - BAT Genesis: allow ( ) [ ] and spaces in the outlet CST No (Laravel PR #10788).

Automated from the Greybox run Execution_2026-10-13 (stagingbatleap). Data: data.json, per company - a QA outlet
whose CST No these tests overwrite (never a customer outlet).
"""

from __future__ import annotations

import pytest

from pages.web.outlets import OutletEditPage

pytestmark = [pytest.mark.web, pytest.mark.ticket("PR1-T13616"), pytest.mark.role("ADMIN"), pytest.mark.destructive]


@pytest.fixture
def outlet(page, base_url, ticket_data):
    return OutletEditPage(page, base_url, ticket_data["outlet_id"]).open()


@pytest.mark.case("TC_WEB_002")
def test_brackets_parentheses_and_spaces_together_are_saved(outlet, evidence):
    value = "CST 123 (Unit) [A]"
    result = outlet.set_cst(value).submit()
    evidence.web(outlet.page, "after_submit")
    assert result.saved, f"not saved: {result.message or result.browser_blocked}"
    assert outlet.stored_cst() == value


@pytest.mark.case("TC_WEB_006")
@pytest.mark.parametrize("value", ["ABC123", "27/AB-1234"])
def test_formats_valid_before_the_change_still_save(outlet, value):
    result = outlet.set_cst(value).submit()
    assert result.saved, f"{value!r} not saved: {result.message or result.browser_blocked}"
    assert outlet.stored_cst() == value


@pytest.mark.case("TC_WEB_009")
@pytest.mark.parametrize("value", ["CST#123", "CST{123}"])
def test_other_special_characters_are_rejected_by_the_server(outlet, value, evidence):
    before = outlet.open_tax_details().cst
    result = outlet.set_cst(value, server_check=True).submit()
    evidence.web(outlet.page, f"rejected_{value}")
    assert not result.saved
    assert "Invalid CST no." in result.message
    assert outlet.stored_cst() == before


@pytest.mark.case("TC_WEB_019")
@pytest.mark.xfail(reason="DEF-CST-01: outlets.cstno is varchar(50) and the rule has no max - the value is cut, "
                          "no error shown", strict=True, raises=AssertionError)
def test_a_255_character_value_is_saved_in_full(outlet):
    value = "(A1)" * 63 + "B12"
    assert len(value) == 255
    result = outlet.set_cst(value).submit()
    assert result.saved
    assert outlet.stored_cst() == value
