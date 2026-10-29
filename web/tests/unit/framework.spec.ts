/** The web framework itself - config, evidence masking, tags, page helpers on an offline page. No portal or secrets. */
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { expect, test } from '@playwright/test';
import { BasePage } from '../../pages/base-page.ts';
import { ConfigError, loadDotenv, loadSettings } from '../../support/config.ts';
import { mask } from '../../support/evidence.ts';
import { tc } from '../../support/tags.ts';

test.describe('config', () => {
  const saved = { ...process.env };
  test.beforeEach(() => {
    for (const key of Object.keys(process.env)) if (/^(BIZOM_|QA_)/.test(key)) delete process.env[key];
    process.env.QA_COMPANY = ''; // no QA_COMPANY: the company comes from the portal host
  });
  test.afterEach(() => {
    process.env = { ...saved };
  });

  test('per-company values and role logins', () => {
    Object.assign(process.env, {
      BIZOM_WEB_URL: 'https://default.example/', BIZOM_WEB_URL_STAGINGX: 'https://x.example', BIZOM_WEB_USER: 'admin1',
      BIZOM_WEB_PASSWORD: 'p1', BIZOM_WEB_ROLE_ZONE_MANAGER_STAGINGX: 'zm/p2', BIZOM_WEB_ROLE_APPROVER_STAGINGX: 'n/a',
    });
    const s = loadSettings('stagingx');
    expect(s.webUrl).toBe('https://x.example');
    expect(s.webLogin()).toEqual({ user: 'admin1', password: 'p1' }); // falls back to the default company's admin
    expect(s.webLogin('zone manager')).toEqual({ user: 'zm', password: 'p2' });
    expect(() => s.webLogin('APPROVER')).toThrow(ConfigError);
    expect(() => s.webLogin('DSR')).toThrow(/BIZOM_WEB_ROLE_DSR/);
    expect(loadSettings('').webUrl).toBe('https://default.example');
    expect(loadSettings('').company).toBe('default');
  });

  test('.env never overrides the environment', () => {
    const file = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'qa-')), '.env');
    fs.writeFileSync(file, "BIZOM_WEB_USER=from_file\nBIZOM_WEB_PASSWORD='quoted'\n# comment\n");
    process.env.BIZOM_WEB_USER = 'from_ci';
    loadDotenv(file);
    expect(process.env.BIZOM_WEB_USER).toBe('from_ci');
    expect(process.env.BIZOM_WEB_PASSWORD).toBe('quoted');
  });
});

test('evidence masks secrets', () => {
  expect(mask({ user: 'a', password: 'b', nested: [{ 'X-Auth-Token': 't' }] }))
    .toEqual({ user: 'a', password: '***', nested: [{ 'X-Auth-Token': '***' }] });
});

test('tc() tags and annotates the ticket and case', () => {
  expect(tc('PR1-T13616', 'TC_WEB_002', '@destructive')).toEqual({
    tag: ['@PR1-T13616', '@TC_WEB_002', '@destructive'],
    annotation: [{ type: 'ticket', description: 'PR1-T13616' }, { type: 'case', description: 'TC_WEB_002' }],
  });
});

test('base page helpers on an offline page', async ({ page }) => {
  await page.setContent(`<label for=n>Name</label><input id=n><button>Save</button><button>Delete outlet</button>
    <div class=alert style='display:block'>Outlet is saved</div><div class=alert style='display:none'>template</div>
    <table><thead><tr><th>Name</th><th>CST</th></tr></thead><tbody><tr><td>QA 1</td><td>A (1)</td></tr></tbody></table>`);
  const p = new BasePage(page, 'https://example.test');
  await p.fill('Name', 'QA 1');
  await expect(page.locator('#n')).toHaveValue('QA 1');
  expect(await p.flash(1_000)).toBe('Outlet is saved');
  expect(await p.tableRows()).toEqual([{ Name: 'QA 1', CST: 'A (1)' }]);
  await expect(p.click('Delete outlet')).rejects.toThrow(/destructive/);
});
