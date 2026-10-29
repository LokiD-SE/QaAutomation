/**
 * BasePage: what every portal page object needs. Page objects in web/pages/ extend it and add their own locators and
 * actions; tests talk to page objects, never to raw selectors.
 */
import type { Locator, Page } from '@playwright/test';

// Onboarding layers that block every click after login. A dialog that is not one of these may be the one under test,
// so it is left alone.
const OVERLAYS = ['text=Got it', '.introjs-skipbutton', '#whatsNewModal .close', "button:has-text('Skip')"];
const FLASH = ['#flash_message', '.flash-message', '#flashMessage', '.alert', '.toast', '.noty_body', '.swal2-html-container',
  '.invalid-feedback', '.help-block', '.error-message', '.ui-dialog-content', '.bootstrap-dialog-message', '.jconfirm-content',
  '.modal.show .modal-body'].join(', ');
export const DESTRUCTIVE = /\b(delete|remove|purge|deactivate|inactivate|reject)\b/i;

const squash = (text: string) => text.split(/\s+/).filter(Boolean).join(' ');

export class BasePage {
  readonly page: Page;
  readonly baseURL: string;
  path = ''; // the page's portal path, e.g. "/outlets/add"

  constructor(page: Page, baseURL: string) {
    this.page = page;
    this.baseURL = baseURL.replace(/\/+$/, '');
  }

  // -- navigation ------------------------------------------------------------------------------------------------
  async open(target: string = this.path, query: Record<string, string | number> = {}): Promise<this> {
    const search = new URLSearchParams(Object.entries(query).map(([k, v]) => [k, String(v)])).toString();
    await this.page.goto(this.baseURL + target + (search ? `?${search}` : ''), { waitUntil: 'domcontentloaded' });
    await this.dismissOverlays();
    return this;
  }

  get currentPath(): string {
    return new URL(this.page.url()).pathname;
  }

  async dismissOverlays(): Promise<string[]> {
    const closed: string[] = [];
    for (const selector of OVERLAYS) {
      const target = this.page.locator(selector).first();
      try {
        if (await target.isVisible()) {
          await target.click({ timeout: 2_000 });
          closed.push(selector);
        }
      } catch {
        // an overlay that vanished is fine
      }
    }
    return closed;
  }

  // -- reading ---------------------------------------------------------------------------------------------------
  /** The message the portal shows after an action (flash bar, toast, field error), or "" when none came. */
  async flash(timeoutMs = 10_000): Promise<string> {
    const visible = this.page.locator(FLASH).filter({ visible: true }); // the page also carries hidden message templates
    try {
      await visible.first().waitFor({ state: 'visible', timeout: timeoutMs });
    } catch {
      return '';
    }
    return (await visible.allInnerTexts()).map(squash).find(Boolean) ?? '';
  }

  /** Rows of a table as {header: cell text}. */
  async tableRows(selector = 'table'): Promise<Record<string, string>[]> {
    const table = this.page.locator(selector).first();
    const headers = (await table.locator('thead th').allInnerTexts()).map((h, i) => squash(h) || `col${i}`);
    const rows: Record<string, string>[] = [];
    for (const row of await table.locator('tbody tr').all()) {
      const cells = (await row.locator('td').allInnerTexts()).map(squash);
      rows.push(Object.fromEntries(cells.map((cell, i) => [headers[i] ?? `col${i}`, cell])));
    }
    return rows;
  }

  // -- acting ----------------------------------------------------------------------------------------------------
  /** A button / link / field by its visible name, falling back to a CSS selector. */
  async control(name: string): Promise<Locator> {
    for (const candidate of [this.page.getByRole('button', { name }), this.page.getByRole('link', { name }),
      this.page.getByLabel(name), this.page.getByPlaceholder(name)]) {
      if (await candidate.count()) return candidate.first();
    }
    return this.page.locator(name).first();
  }

  async click(name: string, { destructive = false } = {}): Promise<void> {
    if (DESTRUCTIVE.test(name) && !destructive) {
      throw new Error(`'${name}' looks destructive - pass { destructive: true } and run on a QA company only`);
    }
    await (await this.control(name)).click();
  }

  async fill(name: string, value: string): Promise<void> {
    const field = await this.control(name);
    await field.fill(value);
    await field.blur(); // many portal inputs commit on blur
  }

  async select(name: string, ...labels: string[]): Promise<void> {
    await (await this.control(name)).selectOption(labels.map((label) => ({ label })));
  }

  /**
   * Set a <select> by option values through jQuery, so bootstrap-select / multiselect widgets and the page's change
   * handlers see it (the portal hides most native selects behind such widgets).
   */
  async selectValues(name: string, values: string[]): Promise<void> {
    await this.page.evaluate(([n, vals]) => {
      const s = document.querySelector<HTMLSelectElement>(`[name="${n}"]`);
      if (!s) return;
      [...s.options].forEach((o) => (o.selected = vals.includes(o.value)));
      const $ = (window as any).jQuery;
      if ($) {
        const $s = $(s);
        $s.trigger('change');
        try { $s.multiselect('refresh'); } catch { /* not a multiselect */ }
        try { $s.selectpicker('refresh'); } catch { /* not a selectpicker */ }
      } else {
        s.dispatchEvent(new Event('change', { bubbles: true }));
      }
    }, [name, values] as const);
  }
}
