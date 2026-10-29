/**
 * Playwright Test for the Bizom web portal. The app suite is pytest + Appium (tests/app, pyproject.toml).
 *
 *   QA_COMPANY=stagingbatleap npx playwright test --project=chromium     every web test against one company
 *   npx playwright test --grep @PR1-T13616                                 one ticket
 *   QA_BROWSERS=chromium,firefox,webkit                                    cross-browser projects
 *   QA_HEADED=1 / QA_TRACE=1                                               watch it / keep traces of failures
 */
import { defineConfig, devices, type Project } from '@playwright/test';
import { loadSettings } from './web/support/config.ts';

const settings = loadSettings();
const DEVICES: Record<string, string> = { chromium: 'Desktop Chrome', firefox: 'Desktop Firefox', webkit: 'Desktop Safari' };
const browsers = (process.env.QA_BROWSERS || 'chromium').split(',').map((b) => b.trim()).filter((b) => b in DEVICES);

export default defineConfig({
  testDir: './web/tests',
  outputDir: './reports/web-artifacts',
  timeout: 180_000, // the portal's outlet form loads ~60 scripts; a save plus a re-read takes ~30 s
  expect: { timeout: 10_000 },
  // Tests in one file run in order on one worker: a ticket's tests share its QA record (data.json). Files run in parallel.
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 2 : undefined,
  reporter: [
    ['list'],
    ['html', { outputFolder: 'reports/web-html', open: 'never' }],
    ['junit', { outputFile: 'reports/web-junit.xml', embedAnnotationsAsProperties: true }],
  ],
  use: {
    baseURL: settings.webUrl || undefined,
    ignoreHTTPSErrors: true,
    headless: settings.headless,
    screenshot: 'only-on-failure',
    // A trace makes a portal save ~4x slower, so it is recorded on the retry of a failed test (CI retries once), or for
    // every test with QA_TRACE=1.
    trace: process.env.QA_TRACE ? 'retain-on-failure' : 'on-first-retry',
    video: 'off',
    actionTimeout: 30_000,
    navigationTimeout: 60_000,
  },
  projects: [
    { name: 'unit', testMatch: /unit\/.*\.spec\.ts$/ },
    ...browsers.map((name): Project => ({
      name,
      testIgnore: /unit\//,
      use: { ...devices[DEVICES[name]], viewport: { width: 1440, height: 900 } },
    })),
  ],
});
