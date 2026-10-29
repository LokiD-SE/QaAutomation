/** Smoke: the admin login works and the dashboard renders. */
import { BasePage } from '../../pages/base-page.ts';
import { expect, test } from '../../support/fixtures.ts';

test('admin reaches the dashboard', { tag: '@smoke' }, async ({ page, portal, evidence }) => {
  const dashboard = await new BasePage(page, portal).open('/users/dashboard');
  await evidence.page(page, 'dashboard');
  expect(page.url()).not.toContain('/users/login');
  expect(dashboard.currentPath).toMatch(/^\/users\/dashboard/);
});
