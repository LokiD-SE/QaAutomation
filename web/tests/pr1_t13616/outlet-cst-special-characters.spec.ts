/**
 * PR1-T13616 - BAT Genesis: allow ( ) [ ] and spaces in the outlet CST No (Laravel PR #10788).
 *
 * Automated from the Greybox run Execution_2026-10-13 (stagingbatleap). Data: data.json, per company - a QA outlet
 * whose CST No these tests overwrite (never a customer outlet).
 */
import { OutletEditPage } from '../../pages/outlets.ts';
import { expect, test } from '../../support/fixtures.ts';
import { tc } from '../../support/tags.ts';

const TICKET = 'PR1-T13616';

test.use({ role: 'ADMIN' });

async function openOutlet(page: import('@playwright/test').Page, portal: string, data: Record<string, string>) {
  return new OutletEditPage(page, portal, data.outlet_id).open();
}

test('brackets, parentheses and spaces together are saved', tc(TICKET, 'TC_WEB_002', '@destructive'),
  async ({ page, portal, ticketData, evidence }) => {
    const outlet = await openOutlet(page, portal, ticketData);
    const value = 'CST 123 (Unit) [A]';
    const result = await outlet.setCst(value).then((o) => o.submit());
    await evidence.page(page, 'after_submit');
    expect(result.saved, `not saved: ${result.message || result.browserBlocked}`).toBe(true);
    expect(await outlet.storedCst()).toBe(value);
  });

for (const value of ['ABC123', '27/AB-1234']) {
  test(`formats valid before the change still save: ${value}`, tc(TICKET, 'TC_WEB_006', '@destructive'),
    async ({ page, portal, ticketData }) => {
      const outlet = await openOutlet(page, portal, ticketData);
      const result = await outlet.setCst(value).then((o) => o.submit());
      expect(result.saved, `'${value}' not saved: ${result.message || result.browserBlocked}`).toBe(true);
      expect(await outlet.storedCst()).toBe(value);
    });
}

for (const value of ['CST#123', 'CST{123}']) {
  test(`other special characters are rejected by the server: ${value}`, tc(TICKET, 'TC_WEB_009', '@destructive'),
    async ({ page, portal, ticketData, evidence }) => {
      const outlet = await openOutlet(page, portal, ticketData);
      const before = await outlet.openTaxDetails().then((o) => o.cst());
      const result = await outlet.setCst(value, { serverCheck: true }).then((o) => o.submit());
      await evidence.page(page, `rejected_${value}`);
      expect(result.saved).toBe(false);
      expect(result.message).toContain('Invalid CST no.');
      expect(await outlet.storedCst()).toBe(before);
    });
}

test('a 255-character value is saved in full', tc(TICKET, 'TC_WEB_019', '@destructive'),
  async ({ page, portal, ticketData }) => {
    test.fail(true, 'DEF-CST-01: outlets.cstno is varchar(50) and the rule has no max - the value is cut, no error shown');
    const outlet = await openOutlet(page, portal, ticketData);
    const value = '(A1)'.repeat(63) + 'B12';
    expect(value).toHaveLength(255);
    const result = await outlet.setCst(value).then((o) => o.submit());
    expect(result.saved).toBe(true);
    expect(await outlet.storedCst()).toBe(value);
  });
