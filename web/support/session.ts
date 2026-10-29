/** Portal login, done once per role and company and reused through Playwright's storage state. */
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import type { Browser, BrowserContextOptions, Page } from '@playwright/test';
import { ROOT, type Login } from './config.ts';

const LOGIN_PATH = '/users/login';
const USERNAME = '#UserUsername, input[name="data[User][username]"], input[name="User[username]"]';
const PASSWORD = '#password, input[name="data[User][password]"], input[name="User[password]"]';
const SUBMIT = '#loginBtn';
const LOGIN_TIMEOUT_MS = 40_000;
export const STATE_DIR = path.join(ROOT, 'reports', '.auth');
const STATE_MAX_AGE_MS = 6 * 3600_000; // a portal session outlives a test run; older states are refreshed

export class LoginError extends Error {}

/**
 * Sign in on `page`. The portal leaves /users/login on success and re-renders it on failure, so the URL is the signal;
 * the landing page can hang on slow resources, so only DOM content is waited for.
 */
export async function login(page: Page, baseURL: string, who: Login): Promise<void> {
  await page.goto(baseURL + LOGIN_PATH, { waitUntil: 'domcontentloaded' });
  await page.fill(USERNAME, who.user);
  await page.fill(PASSWORD, who.password);
  await page.click(SUBMIT);
  try {
    await page.waitForURL((url) => !url.pathname.includes(LOGIN_PATH), { timeout: LOGIN_TIMEOUT_MS, waitUntil: 'domcontentloaded' });
  } catch (error) {
    throw new LoginError(`login as ${who.user} did not leave ${LOGIN_PATH} (still at ${page.url()})`, { cause: error });
  }
  if (!page.url().startsWith(baseURL)) {
    // some roles land on a page the browser cannot render
    await page.goto(baseURL + '/users/dashboard', { waitUntil: 'domcontentloaded' });
  }
}

export function stateFile(baseURL: string, who: Login): string {
  const key = crypto.createHash('sha1').update(`${baseURL}|${who.user}`).digest('hex').slice(0, 12);
  return path.join(STATE_DIR, `${key}.json`);
}

/** A storage-state file for `who` on `baseURL`, logged in once and reused until it is STATE_MAX_AGE_MS old. */
export async function authState(browser: Browser, baseURL: string, who: Login, options: BrowserContextOptions = {}): Promise<string> {
  const file = stateFile(baseURL, who);
  if (fs.existsSync(file) && Date.now() - fs.statSync(file).mtimeMs < STATE_MAX_AGE_MS) return file;
  fs.mkdirSync(STATE_DIR, { recursive: true });
  const context = await browser.newContext(options);
  try {
    await login(await context.newPage(), baseURL, who);
    const temp = `${file}.${process.pid}.tmp`; // parallel workers may log in at once; the rename keeps the file whole
    await context.storageState({ path: temp });
    fs.renameSync(temp, file);
  } finally {
    await context.close();
  }
  return file;
}
