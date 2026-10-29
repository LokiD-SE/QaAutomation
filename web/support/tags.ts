/**
 * Traceability: every test names its ticket and case. Both become tags (`--grep @PR1-T13616`, `--grep @TC_WEB_002`) and
 * annotations, which the JUnit report carries as properties - test -> ticket -> case -> defect.
 *
 *   test('brackets are saved', tc('PR1-T13616', 'TC_WEB_002'), async ({ page }) => { ... });
 *   test('...', tc('PR1-T13616', 'TC_WEB_009', '@destructive'), ...)     extra tags after the case id
 */
import type { TestDetails } from '@playwright/test';

export function tc(ticket: string, caseId: string, ...tags: string[]): TestDetails {
  return {
    tag: [`@${ticket}`, `@${caseId}`, ...tags],
    annotation: [
      { type: 'ticket', description: ticket },
      { type: 'case', description: caseId },
    ],
  };
}
