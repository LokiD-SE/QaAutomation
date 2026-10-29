/** Outlet pages: /outlets/edit/{id} and /outlets/view/{id}. */
import type { Page } from '@playwright/test';
import { BasePage } from './base-page.ts';

const CST = '#OutletCstno';
const PHONE = '#libphonenumberId';
const SUBMIT = "#editoutlet, #outletsubmit, form input[type=submit][value='Submit'], form input[value='Submit'], form button:text-is('Submit')";

export type SaveResult = {
  saved: boolean; // the portal moved on to the outlet's view page
  message: string; // flash / validation text shown
  browserBlocked: string; // the browser's own pattern message when it refused to submit
};

export class OutletEditPage extends BasePage {
  readonly outletId: string;
  readonly dialogs: string[] = [];

  constructor(page: Page, baseURL: string, outletId: string | number) {
    super(page, baseURL);
    this.outletId = String(outletId);
    this.path = `/outlets/edit/${this.outletId}`;
    page.on('dialog', (dialog) => {
      this.dialogs.push(dialog.message());
      void dialog.dismiss();
    });
  }

  /**
   * Data set-up, not the behaviour under test: a mandatory outlet attribute left empty on a QA outlet blocks every save
   * ("Please select Outlet Attributes"); pick the first option, as the outlet's creation did.
   */
  async fillMissingRequired(): Promise<string[]> {
    const empty = await this.page.evaluate(() => [...document.querySelectorAll<HTMLSelectElement>('select[name^="data[dynamic_properties]"]')]
      .filter((s) => s.required || s.closest('.required'))
      .filter((s) => ![...s.options].some((o) => o.selected && o.value))
      .map((s) => ({ name: s.name, first: [...s.options].map((o) => o.value).find(Boolean) ?? '' })));
    const filled: string[] = [];
    for (const { name, first } of empty) {
      if (!first) continue;
      await this.selectValues(name, [first]);
      filled.push(name);
    }
    return filled;
  }

  async openTaxDetails(): Promise<this> {
    if (!(await this.page.locator(CST).isVisible())) {
      await this.page.getByText('Tax Details', { exact: true }).first().click();
      await this.page.locator(CST).waitFor({ state: 'visible' });
    }
    return this;
  }

  async cst(): Promise<string> {
    return this.page.locator(CST).inputValue();
  }

  /** Type the CST No. `serverCheck` drops the browser's pattern so the value reaches the server rule. */
  async setCst(value: string, { serverCheck = false } = {}): Promise<this> {
    await this.openTaxDetails();
    await this.page.fill(CST, value);
    if (serverCheck) await this.page.locator(CST).evaluate((el) => el.removeAttribute('pattern'));
    return this;
  }

  /**
   * The phone widget (intl-tel-input) validates the stored number on load, before its utils.js has arrived, and marks
   * a valid number with the class "error"; the submit handler then refuses with "Enter valid phone number." - not the
   * behaviour under test. Wait for the library (it reformats the number: "5391834987" -> "539 183 49 87"), then let the
   * widget re-run its own check, which clears the stale mark. A number that really is invalid stays marked.
   */
  async waitPhoneChecked(timeoutMs = 15_000): Promise<void> {
    const phone = this.page.locator(PHONE);
    if (!(await phone.count()) || !(await phone.inputValue())) return;
    try {
      await this.page.waitForFunction((sel) => /\s/.test(document.querySelector<HTMLInputElement>(sel)?.value ?? ''), PHONE, { timeout: timeoutMs });
    } catch {
      return; // a number the widget cannot format; the save will say why
    }
    await phone.evaluate((el) => (window as any).jQuery?.(el).trigger('blur'));
  }

  async submit(): Promise<SaveResult> {
    await this.fillMissingRequired();
    await this.waitPhoneChecked();
    const before = this.page.url();
    const button = this.page.locator(SUBMIT).first();
    await button.scrollIntoViewIfNeeded();
    await button.click();
    try {
      await this.page.waitForURL((url) => url.href !== before, { timeout: 20_000, waitUntil: 'domcontentloaded' });
    } catch {
      // staying on the form is a valid outcome (validation)
    }
    const onForm = this.page.url().includes('/outlets/edit');
    const browserBlocked = onForm
      ? await this.page.evaluate((sel) => document.querySelector<HTMLInputElement>(sel)?.validationMessage ?? '', CST)
      : '';
    const saved = new RegExp(`/outlets/view/${this.outletId}\\b`).test(this.page.url());
    return { saved, message: await this.flash(3_000), browserBlocked };
  }

  /** The CST No the portal has now (re-read from a fresh edit page). */
  async storedCst(): Promise<string> {
    await this.open();
    await this.openTaxDetails();
    return this.cst();
  }
}
