/**
 * Settings from the environment and `.env` - the same variable names Greybox (and the app suite's qa/config.py) use,
 * so one .env serves all three.
 *
 *   BIZOM_WEB_URL / BIZOM_WEB_USER / BIZOM_WEB_PASSWORD   default company
 *   BIZOM_WEB_ROLE_<ROLE>=user/password                     a login per role (spaces as underscores; n/a = none)
 *   <any of the above>_<COMPANY>                            per-company values, picked with QA_COMPANY
 *
 * Secrets live only in `.env` (gitignored) or CI secrets - never in the code or the test data.
 */
import fs from 'node:fs';
import path from 'node:path';

export const ROOT = path.resolve(import.meta.dirname, '..', '..');
const NOT_APPLICABLE = 'n/a';

/** A setting the test needs is missing - reported as a skip, never as a product failure. */
export class ConfigError extends Error {}

export type Login = { user: string; password: string };

/** KEY=value lines into process.env; values already set win (CI secrets, the shell). */
export function loadDotenv(file = path.join(ROOT, '.env')): void {
  if (!fs.existsSync(file)) return;
  for (const raw of fs.readFileSync(file, 'utf-8').split(/\r?\n/)) {
    const line = raw.trim();
    if (!line || line.startsWith('#') || !line.includes('=')) continue;
    const at = line.indexOf('=');
    const key = line.slice(0, at).trim();
    if (process.env[key] === undefined) process.env[key] = line.slice(at + 1).trim().replace(/^["']|["']$/g, '');
  }
}

export class Settings {
  company: string;
  webUrl = '';
  webUser = '';
  webPassword = '';
  headless = true;

  constructor(company: string) {
    this.company = company;
  }

  /** `key` for this company (KEY_<COMPANY>), else the default one. */
  env(key: string): string {
    if (this.company) {
      const value = process.env[`${key}_${this.company.toUpperCase()}`];
      if (value !== undefined) return value.trim();
    }
    return (process.env[key] ?? '').trim();
  }

  webLogin(role = ''): Login {
    if (role) {
      const name = `BIZOM_WEB_ROLE_${role.toUpperCase().replace(/ /g, '_')}`;
      const raw = this.env(name);
      if (raw.toLowerCase() === NOT_APPLICABLE) {
        throw new ConfigError(`web role ${role} has no login on ${this.company || 'this company'} (n/a)`);
      }
      const at = raw.indexOf('/');
      if (at > 0 && at < raw.length - 1) return { user: raw.slice(0, at), password: raw.slice(at + 1) };
      if (!['ADMIN', 'DEFAULT'].includes(role.toUpperCase())) {
        throw new ConfigError(`no web login for role ${role}: set ${name}=user/password in .env`);
      }
    }
    if (!(this.webUser && this.webPassword)) {
      throw new ConfigError('no default web login: set BIZOM_WEB_USER / _PASSWORD in .env');
    }
    return { user: this.webUser, password: this.webPassword };
  }
}

export function loadSettings(company?: string): Settings {
  loadDotenv();
  const s = new Settings((company ?? process.env.QA_COMPANY ?? '').trim().toLowerCase());
  s.webUrl = s.env('BIZOM_WEB_URL').replace(/\/+$/, '');
  s.webUser = s.env('BIZOM_WEB_USER');
  s.webPassword = s.env('BIZOM_WEB_PASSWORD');
  if (!s.company && s.webUrl) {
    // https://stagingbatleap.bizomstaging.in -> stagingbatleap (picks the test data)
    s.company = s.webUrl.replace(/^https?:\/\//, '').split('.')[0].toLowerCase();
  }
  s.headless = ['', '0', 'false'].includes(process.env.QA_HEADED ?? '');
  return s;
}
