"""BasePage: what every portal page object needs. Page objects in pages/web/ subclass it and add their own
locators and actions; tests talk to page objects, never to raw selectors."""

from __future__ import annotations

import re

from playwright.sync_api import Locator, Page

# Onboarding layers that block every click after login. A dialog that is not one of these may be the one under test,
# so it is left alone.
_OVERLAYS = ("text=Got it", ".introjs-skipbutton", "#whatsNewModal .close", "button:has-text('Skip')")
_FLASH = ("#flash_message, .flash-message, #flashMessage, .alert, .toast, .noty_body, .swal2-html-container, .invalid-feedback, .help-block, .error-message, "
          ".ui-dialog-content, .bootstrap-dialog-message, .jconfirm-content, .modal.show .modal-body")
DESTRUCTIVE = re.compile(r"\b(delete|remove|purge|deactivate|inactivate|reject)\b", re.I)


class BasePage:
    path = ""  # the page's portal path, e.g. "/outlets/add"

    def __init__(self, page: Page, base_url: str):
        self.page, self.base_url = page, base_url.rstrip("/")

    # -- navigation --------------------------------------------------------------------------------------------
    def open(self, path: str | None = None, **query) -> BasePage:
        target = path if path is not None else self.path
        if query:
            target += "?" + "&".join(f"{k}={v}" for k, v in query.items())
        self.page.goto(self.base_url + target, wait_until="domcontentloaded")
        self.dismiss_overlays()
        return self

    @property
    def current_path(self) -> str:
        return re.sub(r"^https?://[^/]+", "", self.page.url).split("?")[0]

    def dismiss_overlays(self) -> list[str]:
        closed = []
        for selector in _OVERLAYS:
            target = self.page.locator(selector).first
            try:
                if target.is_visible(timeout=300):
                    target.click()
                    closed.append(selector)
            except Exception:  # noqa: BLE001 - an overlay that vanished is fine
                pass
        return closed

    # -- reading -------------------------------------------------------------------------------------------------
    def flash(self, timeout_ms: int = 10_000) -> str:
        """The message the portal shows after an action (flash bar, toast, field error), or "" when none came."""
        visible = self.page.locator(_FLASH).filter(visible=True)  # the page also carries hidden message templates
        try:
            visible.first.wait_for(state="visible", timeout=timeout_ms)
        except Exception:  # noqa: BLE001
            return ""
        texts = [" ".join(t.split()) for t in visible.all_inner_texts()]
        return next((t for t in texts if t), "")

    def table_rows(self, selector: str = "table") -> list[dict[str, str]]:
        """Rows of a table as {header: cell text}."""
        table = self.page.locator(selector).first
        headers = [" ".join(h.split()) or f"col{i}" for i, h in enumerate(table.locator("thead th").all_inner_texts())]
        rows = []
        for row in table.locator("tbody tr").all():
            cells = [" ".join(c.split()) for c in row.locator("td").all_inner_texts()]
            rows.append({headers[i] if i < len(headers) else f"col{i}": cell for i, cell in enumerate(cells)})
        return rows

    # -- acting --------------------------------------------------------------------------------------------------
    def control(self, name: str) -> Locator:
        """A button / link / field by its visible name, falling back to a CSS selector."""
        for candidate in (self.page.get_by_role("button", name=name), self.page.get_by_role("link", name=name),
                          self.page.get_by_label(name), self.page.get_by_placeholder(name)):
            if candidate.count():
                return candidate.first
        return self.page.locator(name).first

    def click(self, name: str, destructive: bool = False) -> None:
        if DESTRUCTIVE.search(name) and not destructive:
            raise PermissionError(f"'{name}' looks destructive - pass destructive=True and run on a QA company only")
        self.control(name).click()

    def fill(self, name: str, value: str) -> None:
        field = self.control(name)
        field.fill(value)
        field.blur()  # many portal inputs commit on blur

    def select(self, name: str, *labels: str) -> None:
        self.control(name).select_option(label=list(labels) if len(labels) > 1 else labels[0])

    def select_values(self, name: str, values: list[str]) -> None:
        """Set a <select> by option values through jQuery, so bootstrap-select / multiselect widgets and the
        page's change handlers see it (the portal hides most native selects behind such widgets)."""
        self.page.evaluate("""([n, vals]) => { const s = document.querySelector(`[name="${n}"]`); if (!s) return;
            [...s.options].forEach(o => o.selected = vals.includes(o.value));
            if (window.jQuery) { const $s = jQuery(s); $s.trigger('change');
                try { $s.multiselect('refresh'); } catch (e) {} try { $s.selectpicker('refresh'); } catch (e) {} }
            else s.dispatchEvent(new Event('change', {bubbles: true})); }""", [name, values])
