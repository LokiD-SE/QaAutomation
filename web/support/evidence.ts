/** Evidence a test keeps: screenshots and JSON, attached to the test's report entry and saved in its output folder. */
import type { Page, TestInfo } from '@playwright/test';

const SECRET_KEYS = /pass(word)?|token|secret|authorization|cookie/i;

/** A copy with password / token values masked - evidence is shared, secrets never are. */
export function mask(data: unknown): unknown {
  if (Array.isArray(data)) return data.map(mask);
  if (data && typeof data === 'object') {
    return Object.fromEntries(Object.entries(data).map(([k, v]) => [k, SECRET_KEYS.test(k) ? '***' : mask(v)]));
  }
  return data;
}

export class Evidence {
  private readonly info: TestInfo;

  constructor(info: TestInfo) {
    this.info = info;
  }

  async page(page: Page, label: string): Promise<string> {
    const file = this.info.outputPath(`${label.replace(/[^\w.-]+/g, '_')}.png`);
    await page.screenshot({ path: file, fullPage: true });
    await this.info.attach(label, { path: file, contentType: 'image/png' });
    return file;
  }

  async json(label: string, data: unknown): Promise<void> {
    await this.info.attach(label, { body: JSON.stringify(mask(data), null, 1), contentType: 'application/json' });
  }
}
