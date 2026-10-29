/**
 * Explore portal pages before writing tests: what each shows, its controls and their selectors.
 *
 *   node web/explore/page-inventory.ts /outlets/edit/1747 /claims/add [--role ADMIN] [--company stagingbatleap] [--headed]
 *
 * Writes explore/out/web/<page>/ - a full-page screenshot and inventory.json (headings, buttons, links, fields with
 * name / id / label, selects with their options, tables with headers). Read-only: nothing is clicked or saved.
 */
import fs from 'node:fs';
import path from 'node:path';
import { parseArgs } from 'node:util';
import { chromium } from '@playwright/test';
import { BasePage } from '../pages/base-page.ts';
import { ROOT, loadSettings } from '../support/config.ts';
import { authState } from '../support/session.ts';

const OUT = path.join(ROOT, 'explore', 'out', 'web');

function inventory() {
  const vis = (e: Element) => !!((e as HTMLElement).offsetParent || e.getClientRects().length);
  const txt = (e: Element) => ((e as HTMLElement).innerText || (e as HTMLInputElement).value || '').trim().replace(/\s+/g, ' ').slice(0, 80);
  const label = (e: Element) => {
    const l = e.id && document.querySelector(`label[for="${e.id}"]`);
    return l ? txt(l) : '';
  };
  return {
    title: document.title,
    headings: [...document.querySelectorAll('h1,h2,h3,h4,legend,.panel-title')].filter(vis).map(txt).filter(Boolean),
    buttons: [...document.querySelectorAll<HTMLButtonElement>('button,input[type=submit],input[type=button],a.btn')].filter(vis)
      .map((e) => ({ text: txt(e), id: e.id, name: e.name || '' })),
    fields: [...document.querySelectorAll<HTMLInputElement>('input:not([type=hidden]),textarea')].map((e) => ({
      name: e.name, id: e.id, type: e.type, label: label(e), placeholder: e.placeholder || '',
      pattern: e.getAttribute('pattern') || '', maxlength: e.maxLength > 0 ? e.maxLength : null, visible: vis(e) })),
    selects: [...document.querySelectorAll<HTMLSelectElement>('select')].map((e) => ({ name: e.name, id: e.id, label: label(e),
      multiple: e.multiple, options: [...e.options].slice(0, 25).map((o) => o.text.trim()) })),
    tables: [...document.querySelectorAll('table')].filter(vis).map((t) => [...t.querySelectorAll('thead th')].map(txt)),
  };
}

const { values, positionals } = parseArgs({
  allowPositionals: true,
  options: { role: { type: 'string', default: 'ADMIN' }, company: { type: 'string' }, headed: { type: 'boolean', default: false } },
});
const settings = loadSettings(values.company);
if (!settings.webUrl || !positionals.length) {
  console.error(!settings.webUrl ? 'set BIZOM_WEB_URL in .env' : 'usage: node web/explore/page-inventory.ts <path> [<path> ...]');
  process.exit(2);
}
const browser = await chromium.launch({ headless: !values.headed });
try {
  const options = { viewport: { width: 1440, height: 900 }, ignoreHTTPSErrors: true };
  const context = await browser.newContext({ ...options, storageState: await authState(browser, settings.webUrl, settings.webLogin(values.role), options) });
  const page = await context.newPage();
  for (const target of positionals) {
    await new BasePage(page, settings.webUrl).open(target);
    await page.waitForTimeout(2_500);
    const folder = path.join(OUT, target.replace(/^\/+|\/+$/g, '').replace(/[^\w.-]+/g, '_') || 'root');
    fs.mkdirSync(folder, { recursive: true });
    await page.screenshot({ path: path.join(folder, 'page.png'), fullPage: true });
    const found = { ...(await page.evaluate(inventory)), url: page.url().replace(settings.webUrl, '') };
    fs.writeFileSync(path.join(folder, 'inventory.json'), JSON.stringify(found, null, 1));
    console.log(`${target}: ${found.fields.length} fields, ${found.buttons.length} buttons -> ${folder}`);
  }
} finally {
  await browser.close();
}
