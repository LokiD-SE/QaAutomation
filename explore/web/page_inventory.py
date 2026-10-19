"""Explore portal pages before writing tests: what each shows, its controls and their selectors.

    python -m explore.web.page_inventory /outlets/edit/1747 /claims/add --role ADMIN [--company stagingbatleap] [--headed]

Writes explore/out/web/<page>/ - a full-page screenshot and inventory.json (headings, buttons, links, fields with
name / id / label, selects with their options, tables with headers). Read-only: nothing is clicked or saved.
"""

from __future__ import annotations

import argparse
import json
import re
import sys

from playwright.sync_api import sync_playwright

from qa.config import ROOT, settings
from qa.web.page import BasePage
from qa.web.session import auth_state

OUT = ROOT / "explore" / "out" / "web"

INVENTORY_JS = """() => {
  const vis = e => !!(e.offsetParent || e.getClientRects().length);
  const txt = e => (e.innerText || e.value || '').trim().replace(/\\s+/g, ' ').slice(0, 80);
  const label = e => { const l = e.id && document.querySelector(`label[for="${e.id}"]`); return l ? txt(l) : ''; };
  return {
    title: document.title,
    headings: [...document.querySelectorAll('h1,h2,h3,h4,legend,.panel-title')].filter(vis).map(txt).filter(Boolean),
    buttons: [...document.querySelectorAll('button,input[type=submit],input[type=button],a.btn')].filter(vis)
      .map(e => ({text: txt(e), id: e.id, name: e.name || ''})),
    fields: [...document.querySelectorAll('input:not([type=hidden]),textarea')].map(e => ({
      name: e.name, id: e.id, type: e.type, label: label(e), placeholder: e.placeholder || '',
      pattern: e.getAttribute('pattern') || '', maxlength: e.maxLength > 0 ? e.maxLength : null, visible: vis(e)})),
    selects: [...document.querySelectorAll('select')].map(e => ({name: e.name, id: e.id, label: label(e),
      multiple: e.multiple, options: [...e.options].slice(0, 25).map(o => o.text.trim())})),
    tables: [...document.querySelectorAll('table')].filter(vis).map(t => [...t.querySelectorAll('thead th')].map(txt)),
  };
}"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--role", default="ADMIN")
    parser.add_argument("--company", default=None)
    parser.add_argument("--headed", action="store_true")
    args = parser.parse_args(argv)
    cfg = settings(args.company)
    if not cfg.web_url:
        print("set BIZOM_WEB_URL in .env", file=sys.stderr)
        return 2
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=not args.headed)
        context = browser.new_context(storage_state=str(auth_state(browser, cfg.web_url, cfg.web_login(args.role))),
                                      viewport={"width": 1440, "height": 900}, ignore_https_errors=True)
        page = context.new_page()
        for path in args.paths:
            BasePage(page, cfg.web_url).open(path)
            page.wait_for_timeout(2500)
            folder = OUT / re.sub(r"[^\w.-]+", "_", path.strip("/") or "root")
            folder.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(folder / "page.png"), full_page=True)
            inventory = page.evaluate(INVENTORY_JS)
            inventory["url"] = page.url.replace(cfg.web_url, "")
            (folder / "inventory.json").write_text(json.dumps(inventory, indent=1), encoding="utf-8")
            print(f"{path}: {len(inventory['fields'])} fields, {len(inventory['buttons'])} buttons -> {folder}")
        browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
