/**
 * The fixtures every web test imports instead of @playwright/test's own:
 *
 *   page / context   logged in as the test's role (`test.use({ role: 'APPROVER' })`, ADMIN by default) through a cached
 *                    storage state, so Playwright's own failure screenshots and traces keep working
 *   asRole(role)     a second logged-in page for multi-user flows (closed after the test)
 *   evidence         screenshots / JSON attached to the report
 *   ticketData       the spec folder's data.json entry for the run's company (QA_COMPANY)
 *
 * Missing settings or logins skip the test with the reason; they are never reported as product failures.
 */
import fs from 'node:fs';
import path from 'node:path';
import { test as base, expect, type Page } from '@playwright/test';
import { ConfigError, loadSettings, type Settings } from './config.ts';
import { Evidence } from './evidence.ts';
import { authState } from './session.ts';

type Options = { role: string };
type Fixtures = {
  settings: Settings;
  portal: string;
  asRole: (role: string) => Promise<Page>;
  evidence: Evidence;
  ticketData: Record<string, string>;
};

function loginOf(settings: Settings, role: string) {
  try {
    return settings.webLogin(role);
  } catch (error) {
    if (error instanceof ConfigError) test.skip(true, error.message);
    throw error;
  }
}

export const test = base.extend<Options & Fixtures>({
  role: ['ADMIN', { option: true }],

  settings: async ({}, use) => {
    await use(loadSettings());
  },

  /** The portal's base URL; the test skips when none is configured. */
  portal: async ({ settings, baseURL }, use) => {
    const url = (baseURL || settings.webUrl).replace(/\/+$/, '');
    test.skip(!url, 'no portal URL: set BIZOM_WEB_URL (or BIZOM_WEB_URL_<COMPANY>) in .env');
    await use(url);
  },

  storageState: async ({ browser, settings, role, portal, ignoreHTTPSErrors, viewport }, use) => {
    await use(await authState(browser, portal, loginOf(settings, role), { ignoreHTTPSErrors, viewport }));
  },

  asRole: async ({ browser, settings, portal, ignoreHTTPSErrors, viewport }, use) => {
    const contexts: Awaited<ReturnType<typeof browser.newContext>>[] = [];
    await use(async (role) => {
      const options = { baseURL: portal, ignoreHTTPSErrors, viewport };
      const context = await browser.newContext({ ...options, storageState: await authState(browser, portal, loginOf(settings, role), options) });
      contexts.push(context);
      return context.newPage();
    });
    for (const context of contexts) await context.close();
  },

  evidence: async ({}, use, testInfo) => {
    await use(new Evidence(testInfo));
  },

  ticketData: async ({ settings }, use, testInfo) => {
    const file = path.join(path.dirname(testInfo.file), 'data.json');
    test.skip(!fs.existsSync(file), `no data.json beside ${path.basename(testInfo.file)}`);
    const data = JSON.parse(fs.readFileSync(file, 'utf-8'));
    test.skip(!(settings.company in data), `no test data for company '${settings.company}' in ${path.relative(process.cwd(), file)}`);
    await use(data[settings.company]);
  },
});

export { expect };
