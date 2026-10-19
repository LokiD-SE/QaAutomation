"""Outlet pages: /outlets/edit/{id} and /outlets/view/{id}."""

from __future__ import annotations

import re
from dataclasses import dataclass

from qa.web.page import BasePage

CST = "#OutletCstno"
PHONE = "#libphonenumberId"
SUBMIT = "#editoutlet, #outletsubmit, form input[type=submit][value='Submit'], form input[value='Submit'], form button:text-is('Submit')"


@dataclass
class SaveResult:
    saved: bool          # the portal moved on to the outlet's view page
    message: str         # flash / validation text shown
    browser_blocked: str  # the browser's own pattern message when it refused to submit


class OutletEditPage(BasePage):
    def __init__(self, page, base_url: str, outlet_id: str | int):
        super().__init__(page, base_url)
        self.outlet_id = str(outlet_id)
        self.path = f"/outlets/edit/{self.outlet_id}"
        self.dialogs: list[str] = []
        page.on("dialog", lambda d: (self.dialogs.append(d.message), d.dismiss()))

    def fill_missing_required(self) -> list[str]:
        """Data set-up, not the behaviour under test: a mandatory outlet attribute left empty on a QA outlet blocks
        every save ("Please select Outlet Attributes"); pick the first option, as the outlet's creation did."""
        filled = []
        for name in self.page.evaluate("""() => [...document.querySelectorAll('select[name^="data[dynamic_properties]"]')]
                .filter(s => s.required || s.closest('.required')).filter(s => ![...s.options].some(o => o.selected && o.value))
                .map(s => s.name)"""):
            first = self.page.evaluate(f"""() => [...document.querySelector('[name="{name}"]').options]
                .map(o => o.value).filter(v => v)[0] || ''""")
            if first:
                self.select_values(name, [first])
                filled.append(name)
        return filled

    def open_tax_details(self) -> OutletEditPage:
        if not self.page.locator(CST).is_visible():
            self.page.get_by_text("Tax Details", exact=True).first.click()
            self.page.locator(CST).wait_for(state="visible")
        return self

    @property
    def cst(self) -> str:
        return self.page.locator(CST).input_value()

    def set_cst(self, value: str, server_check: bool = False) -> OutletEditPage:
        """Type the CST No. `server_check` drops the browser's pattern so the value reaches the server rule."""
        self.open_tax_details()
        self.page.fill(CST, value)
        if server_check:
            self.page.evaluate(f"() => document.querySelector('{CST}').removeAttribute('pattern')")
        return self

    def wait_phone_checked(self, timeout_ms: int = 15_000) -> None:
        """The phone widget takes over the stored number asynchronously after load (it reformats it); a submit before
        that is refused with "Enter valid phone number." - not the behaviour under test. Do not focus / blur the field:
        that makes the widget re-check it and the same refusal comes back."""
        phone = self.page.locator(PHONE)
        if not phone.count() or not phone.input_value():
            return
        try:  # the widget reformats the stored number once its library has loaded ("5391834987" -> "539 183 49 87")
            self.page.wait_for_function(f"() => /\\s/.test(document.querySelector('{PHONE}').value)", timeout=timeout_ms)
        except Exception:  # noqa: BLE001 - a number the widget cannot format; the save will say why
            pass

    def submit(self) -> SaveResult:
        self.fill_missing_required()
        self.wait_phone_checked()
        before = self.page.url
        button = self.page.locator(SUBMIT).first
        button.scroll_into_view_if_needed()
        button.click()
        try:
            self.page.wait_for_url(lambda url: url != before, timeout=20_000, wait_until="domcontentloaded")
        except Exception:  # noqa: BLE001 - staying on the form is a valid outcome (validation)
            pass
        blocked = self.page.evaluate(f"() => document.querySelector('{CST}')?.validationMessage || ''") \
            if "/outlets/edit" in self.page.url else ""
        saved = bool(re.search(rf"/outlets/view/{self.outlet_id}\b", self.page.url))
        return SaveResult(saved, self.flash(timeout_ms=3_000), blocked)

    def stored_cst(self) -> str:
        """The CST No the portal has now (re-read from a fresh edit page)."""
        self.open()
        self.open_tax_details()
        return self.cst
