/**
 * PR1-T13616 - PR1-T13616_BAT_Genesis_Support_special_characters
 *
 * Scaffolded by Greybox `qa-run automate PR1-T13616`: one test.fixme stub per verified case. Write each against
 * web/pages/ (CLAUDE.md) and keep its tc() ids.
 */
import { expect, test } from '../../support/fixtures.ts';
import { tc } from '../../support/tags.ts';

const TICKET = 'PR1-T13616';

test.use({ role: 'ADMIN' });

/**
 * TC_WEB_001 - Verify Admin can save a Malaysian business registration number with parentheses in CST No on Edit Outlet
 *
 * Greybox: Pass on Execution_2026-10-13 (stagingbatleap)
 * Actual: Edit RETAILERS 1747 > Tax Details > Outlet Cst no: '201701041932 (1256105-X)': browser valid=True, after Submit /outlets/view/1747 ['Outlet is saved successfully'], Edit shows '201701041932 (1256105-X)'
 *
 * Preconditions:
 *     Setting default configuration=default (no company setting gates the CST No validation; after PR #10788 the rule allows letters, digits, '/', '-', '(', ')', '[', ']' and spaces for every company). User workflow "Edit Outlet" enabled. Admin user of the company under test (Staging Batleap) can log in on https://stagingbatleap.bizomstaging.in. Active retailer outlet {outletId} (not a distributor outlet) exists and is visible to the Admin. CST No (cst_no) field is shown, editable and not mandatory under Tax Details (default outlet form field configuration).
 *
 * Steps:
 *     1. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and click on the Tax Details section
 *     2. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and enter '201701041932 (1256105-X)' in the CST No field
 *     3. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and click on Submit
 *     4. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and check the CST No field under Tax Details
 *
 * Expected:
 *     1. User should be able to login to web and see the Tax Details section expanded with the CST No field
 *     2. User should be able to login to web and enter '201701041932 (1256105-X)' in CST No without any validation error
 *     3. User should be able to login to web and save the outlet; System should redirect to /outlets/view/{outletId} with the message 'Outlet is saved successfully' and no 'Invalid CST no.' error
 *     4. User should be able to login to web and see CST No pre-filled with '201701041932 (1256105-X)'
 */
test.fixme('Verify Admin can save a Malaysian business registration number', tc(TICKET, 'TC_WEB_001'), async () => {
  // not automated yet - see tickets/PR1-T13616/cases.json
});

/**
 * TC_WEB_003 - Verify Admin can create an outlet with a CST No containing slash, hyphen, parentheses, square brackets and space on Add Outlet
 *
 * Greybox: Pass on Execution_2026-10-13 (stagingbatleap)
 * Actual: Add RETAILERS: filled Name 'QA CST Bracket Outlet 01', State İstanbul, District İstanbul_Avr, City, Area, Beat A, Outlet Category RETAILER, Outlet Attributes, Phone, License No dates (license_no end date is mandatory on this company), opened Tax Details and entered Outlet Cst no 'ABC-123/45(6)[7] 8'
 *
 * Preconditions:
 *     Setting default configuration=default (no company setting gates the CST No validation; after PR #10788 the rule allows letters, digits, '/', '-', '(', ')', '[', ']' and spaces for every company). Admin user of the company under test (Staging Batleap) can log in on https://stagingbatleap.bizomstaging.in. An active state, area and beat exist for the Add Outlet mandatory fields. Outlet name {outletName} is unique (no duplicate-outlet popup). CST No (cst_no) field is shown and editable under Tax Details on Add Outlet.
 *
 * Steps:
 *     1. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/add and fill the mandatory fields (Name '{outletName}', State, Area, Beat)
 *     2. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/add and click on the Tax Details section
 *     3. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/add and enter 'ABC-123/45(6)[7] 8' in the CST No field
 *     4. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/add and click on Submit
 *
 * Expected:
 *     1. User should be able to login to web and fill all mandatory outlet fields
 *     2. User should be able to login to web and see the Tax Details section expanded with the CST No field
 *     3. User should be able to login to web and enter 'ABC-123/45(6)[7] 8' with no browser 'Please match the requested format.' tooltip
 *     4. User should be able to login to web and create the outlet; System should redirect to /outlets/view/{newOutletId} with the message 'The outlet id {newOutletId} has been saved'
 */
test.fixme('Verify Admin can create an outlet with a CST', tc(TICKET, 'TC_WEB_003'), async () => {
  // not automated yet - see tickets/PR1-T13616/cases.json
});

/**
 * TC_WEB_004 - Verify other outlet details can be edited and saved when the stored CST No already contains brackets
 *
 * Greybox: Pass on Execution_2026-10-13 (stagingbatleap)
 * Actual: Edit RETAILERS 1747 with stored Outlet Cst no '201701041932 (1256105-X)', Name changed to 'QA CST Bracket Outlet 01 QA' (Tax Details untouched): after Submit /outlets/view/1747 messages ['Outlet is saved successfully']; Edit shows Name 'QA CST Bracket Outlet 01 QA', Outlet Cst no '201701041932 (1256
 *
 * Preconditions:
 *     Setting default configuration=default (no company setting gates the CST No validation; after PR #10788 the rule allows letters, digits, '/', '-', '(', ')', '[', ']' and spaces for every company). User workflow "Edit Outlet" enabled. Admin user of the company under test (Staging Batleap) can log in on https://stagingbatleap.bizomstaging.in. Active retailer outlet {outletId} has outlets.cstno='201701041932 (1256105-X)' (saved in TC_WEB_001).
 *
 * Steps:
 *     1. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and check the CST No field under Tax Details
 *     2. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and enter '{outletName} QA' in the Name field
 *     3. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and click on Submit
 *
 * Expected:
 *     1. User should be able to login to web and see CST No pre-filled with '201701041932 (1256105-X)'
 *     2. User should be able to login to web and enter the new outlet name
 *     3. User should be able to login to web and save the outlet with the message 'Outlet is saved successfully' and no 'Invalid CST no.' error
 */
test.fixme('Verify other outlet details can be edited and saved', tc(TICKET, 'TC_WEB_004'), async () => {
  // not automated yet - see tickets/PR1-T13616/cases.json
});

/**
 * TC_WEB_005 - Verify the ticket's sample registration number with a leading space, inner spaces and lowercase letter is accepted and saved trimmed
 *
 * Greybox: Pass on Execution_2026-10-13 (stagingbatleap)
 * Actual: Edit RETAILERS 1747 > Tax Details > Outlet Cst no: ' 201701041932 ( 1256105 -x)': browser valid=True, after Submit /outlets/view/1747 ['Outlet is saved successfully'], Edit shows '201701041932 ( 1256105 -x)'
 *
 * Preconditions:
 *     Setting default configuration=default (no company setting gates the CST No validation; after PR #10788 the rule allows letters, digits, '/', '-', '(', ')', '[', ']' and spaces for every company). User workflow "Edit Outlet" enabled. Admin user of the company under test (Staging Batleap) can log in on https://stagingbatleap.bizomstaging.in. Active retailer outlet {outletId} exists.
 *
 * Steps:
 *     1. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and enter ' 201701041932 ( 1256105 -x)' in the CST No field under Tax Details
 *     2. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and click on Submit
 *     3. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and check the CST No field under Tax Details
 *
 * Expected:
 *     1. User should be able to login to web and enter the value with spaces and the lowercase 'x'
 *     2. User should be able to login to web and save the outlet with the message 'Outlet is saved successfully'
 *     3. User should be able to login to web and see CST No as '201701041932 ( 1256105 -x)' with the leading space removed and the inner spaces kept
 */
test.fixme('Verify the ticket s sample registration number with a', tc(TICKET, 'TC_WEB_005'), async () => {
  // not automated yet - see tickets/PR1-T13616/cases.json
});

/**
 * TC_WEB_007 - Verify CST No can be cleared and the outlet saves when the field is not mandatory
 *
 * Greybox: Pass on Execution_2026-10-13 (stagingbatleap)
 * Actual: Edit RETAILERS 1747 > Tax Details > Outlet Cst no: '': browser valid=True, after Submit /outlets/view/1747 ['Outlet is saved successfully'], Edit shows ''
 *
 * Preconditions:
 *     Setting default configuration=default (no company setting gates the CST No validation; after PR #10788 the rule allows letters, digits, '/', '-', '(', ')', '[', ']' and spaces for every company). User workflow "Edit Outlet" enabled. Admin user of the company under test (Staging Batleap) can log in on https://stagingbatleap.bizomstaging.in. Active retailer outlet {outletId} has a non-empty CST No. cst_no is not marked mandatory.
 *
 * Steps:
 *     1. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and clear the CST No field under Tax Details
 *     2. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and click on Submit
 *     3. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and check the CST No field under Tax Details
 *
 * Expected:
 *     1. User should be able to login to web and clear the CST No field
 *     2. User should be able to login to web and save the outlet with the message 'Outlet is saved successfully' and no 'Invalid CST no.' error
 *     3. User should be able to login to web and see the CST No field blank
 */
test.fixme('Verify CST No can be cleared and the outlet', tc(TICKET, 'TC_WEB_007'), async () => {
  // not automated yet - see tickets/PR1-T13616/cases.json
});

/**
 * TC_WEB_008 - Verify Edit Outlet rejects a CST No containing '@' with the message 'Invalid CST no.'
 *
 * Greybox: Pass on Execution_2026-10-13 (stagingbatleap)
 * Actual: Edit RETAILERS 1747 > Tax Details > Outlet Cst no: '<redacted>': browser valid=False tooltip 'Please match the requested format.', stayed on /outlets/edit/1747, Edit still '201701041932 (1256105-X)'; server check (pattern removed): after Submit /outlets/edit/1747 messages ['Invalid CST no.', 'Please
 *
 * Preconditions:
 *     Setting default configuration=default (no company setting gates the CST No validation; after PR #10788 the rule allows letters, digits, '/', '-', '(', ')', '[', ']' and spaces for every company). User workflow "Edit Outlet" enabled. Admin user of the company under test (Staging Batleap) can log in on https://stagingbatleap.bizomstaging.in. Active retailer outlet {outletId} has CST No '201701041932 (1256105-X)'. The Edit Outlet Submit button posts the form through jQuery, so the server rule (not the browser pattern) decides.
 *
 * Steps:
 *     1. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and enter '<redacted>' in the CST No field under Tax Details
 *     2. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and click on Submit
 *     3. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and reload the page and check the CST No field
 *
 * Expected:
 *     1. User should be able to login to web and enter '<redacted>' in CST No
 *     2. User should be able to login to web and see the save rejected with the message 'Invalid CST no.' and remain on the Edit Outlet page
 *     3. User should be able to login to web and see CST No still '201701041932 (1256105-X)'
 */
test.fixme('Verify Edit Outlet rejects a CST No containing with', tc(TICKET, 'TC_WEB_008'), async () => {
  // not automated yet - see tickets/PR1-T13616/cases.json
});

/**
 * TC_WEB_010 - Verify Add Outlet blocks an invalid CST No in a collapsed Tax Details section and opens the section to show the browser validation
 *
 * Greybox: Pass on Execution_2026-10-13 (stagingbatleap)
 * Actual: Add RETAILERS: '<redacted>' with Tax Details collapsed (True): after Submit stayed on /outlets/add, Tax Details re-opened=True, Outlet Cst no tooltip 'Please match the requested format.', messages [], outlet created=False
 *
 * Preconditions:
 *     Setting default configuration=default (no company setting gates the CST No validation; after PR #10788 the rule allows letters, digits, '/', '-', '(', ')', '[', ']' and spaces for every company). Admin user of the company under test (Staging Batleap) can log in on https://stagingbatleap.bizomstaging.in. An active state, area and beat exist. CST No (cst_no) field is shown and editable under Tax Details on Add Outlet.
 *
 * Steps:
 *     1. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/add and fill the mandatory fields (Name '{outletName}', State, Area, Beat)
 *     2. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/add and click on the Tax Details section and enter '<redacted>' in the CST No field
 *     3. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/add and click on the Tax Details section header to collapse it
 *     4. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/add and click on Submit
 *
 * Expected:
 *     1. User should be able to login to web and fill all mandatory outlet fields
 *     2. User should be able to login to web and enter '<redacted>' in CST No
 *     3. User should be able to login to web and see the Tax Details section collapsed
 *     4. User should be able to login to web and see the Tax Details section re-opened with the browser tooltip 'Please match the requested format.' on CST No; System should not create the outlet
 */
test.fixme('Verify Add Outlet blocks an invalid CST No in', tc(TICKET, 'TC_WEB_010'), async () => {
  // not automated yet - see tickets/PR1-T13616/cases.json
});

/**
 * TC_WEB_011 - Verify Add Outlet browser validation blocks an apostrophe and '#' in CST No
 *
 * Greybox: Pass on Execution_2026-10-13 (stagingbatleap)
 * Actual: Add RETAILERS: 'O'Neil 1256105' with Tax Details collapsed (True): after Submit stayed on /outlets/add, Tax Details re-opened=True, Outlet Cst no tooltip 'Please match the requested format.', messages [], outlet created=False; 'CST#123' with Tax Details collapsed (True): after Submit stayed on /outl
 *
 * Preconditions:
 *     Setting default configuration=default (no company setting gates the CST No validation; after PR #10788 the rule allows letters, digits, '/', '-', '(', ')', '[', ']' and spaces for every company). Admin user of the company under test (Staging Batleap) can log in on https://stagingbatleap.bizomstaging.in. An active state, area and beat exist.
 *
 * Steps:
 *     1. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/add and fill the mandatory fields (Name '{outletName}', State, Area, Beat)
 *     2. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/add and click on the Tax Details section and enter "O'Neil 1256105" in the CST No field
 *     3. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/add and click on Submit
 *     4. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/add and enter 'CST#123' in the CST No field and click on Submit
 *
 * Expected:
 *     1. User should be able to login to web and fill all mandatory outlet fields
 *     2. User should be able to login to web and enter the value with the apostrophe in CST No
 *     3. User should be able to login to web and see the browser tooltip 'Please match the requested format.' on CST No with the outlet not created
 *     4. User should be able to login to web and see the browser tooltip 'Please match the requested format.' on CST No with the outlet not created
 */
test.fixme('Verify Add Outlet browser validation blocks an apostrophe and', tc(TICKET, 'TC_WEB_011'), async () => {
  // not automated yet - see tickets/PR1-T13616/cases.json
});

/**
 * TC_WEB_012 - Verify HTML/script injection in CST No is rejected on Edit Outlet and never executes
 *
 * Greybox: Pass on Execution_2026-10-13 (stagingbatleap)
 * Actual: Edit RETAILERS 1747 > Tax Details > Outlet Cst no: '<script>alert(1)</script>': browser valid=False tooltip 'Please match the requested format.', stayed on /outlets/edit/1747, Edit still '201701041932 (1256105-X)'; server check (pattern removed): after Submit /outlets/edit/1747 messages ['Invalid CS
 *
 * Preconditions:
 *     Setting default configuration=default (no company setting gates the CST No validation; after PR #10788 the rule allows letters, digits, '/', '-', '(', ')', '[', ']' and spaces for every company). User workflow "Edit Outlet" enabled. Admin user of the company under test (Staging Batleap) can log in on https://stagingbatleap.bizomstaging.in. Active retailer outlet {outletId} has CST No '201701041932 (1256105-X)'.
 *
 * Steps:
 *     1. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and enter '<script>alert(1)</script>' in the CST No field and click on Submit
 *     2. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and enter '(1)<img src=x onerror=alert(1)>' in the CST No field and click on Submit
 *     3. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and reload the page and check the CST No field
 *
 * Expected:
 *     1. User should be able to login to web and see the message 'Invalid CST no.' with no JavaScript alert shown
 *     2. User should be able to login to web and see the message 'Invalid CST no.' with no JavaScript alert shown
 *     3. User should be able to login to web and see CST No still '201701041932 (1256105-X)'
 */
test.fixme('Verify HTML script injection in CST No is rejected', tc(TICKET, 'TC_WEB_012'), async () => {
  // not automated yet - see tickets/PR1-T13616/cases.json
});

/**
 * TC_WEB_013 - Verify full-width (Unicode) brackets and accented letters in CST No are rejected on Edit Outlet
 *
 * Greybox: Pass on Execution_2026-10-13 (stagingbatleap)
 * Actual: Edit RETAILERS 1747 > Tax Details > Outlet Cst no: '201701041932（1256105-X）': browser valid=False tooltip 'Please match the requested format.', stayed on /outlets/edit/1747, Edit still '201701041932 (1256105-X)'; server check (pattern removed): after Submit /outlets/edit/1747 messages ['Invalid CST
 *
 * Preconditions:
 *     Setting default configuration=default (no company setting gates the CST No validation; after PR #10788 the rule allows letters, digits, '/', '-', '(', ')', '[', ']' and spaces for every company). User workflow "Edit Outlet" enabled. Admin user of the company under test (Staging Batleap) can log in on https://stagingbatleap.bizomstaging.in. Active retailer outlet {outletId} exists.
 *
 * Steps:
 *     1. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and enter '201701041932（1256105-X）' in the CST No field and click on Submit
 *     2. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and enter 'ABC123é' in the CST No field and click on Submit
 *
 * Expected:
 *     1. User should be able to login to web and see the message 'Invalid CST no.' with the outlet not saved
 *     2. User should be able to login to web and see the message 'Invalid CST no.' with the outlet not saved
 */
test.fixme('Verify full width Unicode brackets and accented letters in', tc(TICKET, 'TC_WEB_013'), async () => {
  // not automated yet - see tickets/PR1-T13616/cases.json
});

/**
 * TC_WEB_014 - Verify the LBT No field still rejects brackets because the change applies to CST No only
 *
 * Greybox: Pass on Execution_2026-10-13 (stagingbatleap)
 * Actual: This company's Edit RETAILERS form has no LBT No field (#OutletLbtno absent, field not configured), so the rule was checked on the server via POST /outlets/edit/1747?isJson=1: lbtno 'LBT (123)' -> {"Result": false, "Reason": "Invalid LBT no."} (HTTP 200, the API's normal failure status - see TC_WEB_
 *
 * Preconditions:
 *     Setting default configuration=default (no company setting gates the CST No validation; after PR #10788 the rule allows letters, digits, '/', '-', '(', ')', '[', ']' and spaces for every company). User workflow "Edit Outlet" enabled. Admin user of the company under test (Staging Batleap) can log in on https://stagingbatleap.bizomstaging.in. Active retailer outlet {outletId} exists. The LBT No (lbt_no) field is shown under Tax Details.
 *
 * Steps:
 *     1. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and enter 'LBT (123)' in the Outlet LBT no field under Tax Details
 *     2. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and click on Submit
 *     3. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and reload the page and check the Outlet LBT no field
 *
 * Expected:
 *     1. User should be able to login to web and enter 'LBT (123)' in Outlet LBT no
 *     2. User should be able to login to web and see the save rejected with the message 'Invalid LBT no.'
 *     3. User should be able to login to web and see the Outlet LBT no field with its earlier value
 */
test.fixme('Verify the LBT No field still rejects brackets because', tc(TICKET, 'TC_WEB_014'), async () => {
  // not automated yet - see tickets/PR1-T13616/cases.json
});

/**
 * TC_WEB_015 - Verify CST No values that start or end with a bracket, slash or hyphen are accepted
 *
 * Greybox: Pass on Execution_2026-10-13 (stagingbatleap)
 * Actual: Edit RETAILERS 1747 > Tax Details > Outlet Cst no: '(1256105-X)': browser valid=True, after Submit /outlets/view/1747 ['Outlet is saved successfully'], Edit shows '(1256105-X)'; '[A1]': browser valid=True, after Submit /outlets/view/1747 ['Outlet is saved successfully'], Edit shows '[A1]'; '-123/':
 *
 * Preconditions:
 *     Setting default configuration=default (no company setting gates the CST No validation; after PR #10788 the rule allows letters, digits, '/', '-', '(', ')', '[', ']' and spaces for every company). User workflow "Edit Outlet" enabled. Admin user of the company under test (Staging Batleap) can log in on https://stagingbatleap.bizomstaging.in. Active retailer outlet {outletId} exists.
 *
 * Steps:
 *     1. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and enter '(1256105-X)' in the CST No field and click on Submit
 *     2. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and enter '[A1]' in the CST No field and click on Submit
 *     3. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and enter '-123/' in the CST No field and click on Submit
 *
 * Expected:
 *     1. User should be able to login to web and save the outlet with the message 'Outlet is saved successfully'
 *     2. User should be able to login to web and save the outlet with the message 'Outlet is saved successfully'
 *     3. User should be able to login to web and save the outlet with the message 'Outlet is saved successfully'
 */
test.fixme('Verify CST No values that start or end with', tc(TICKET, 'TC_WEB_015'), async () => {
  // not automated yet - see tickets/PR1-T13616/cases.json
});

/**
 * TC_WEB_016 - Verify CST No made only of brackets or a single bracket is accepted as the new rule allows
 *
 * Greybox: Pass on Execution_2026-10-13 (stagingbatleap)
 * Actual: Edit RETAILERS 1747 > Tax Details > Outlet Cst no: '()[]': browser valid=True, after Submit /outlets/view/1747 ['Outlet is saved successfully'], Edit shows '()[]'; '(': browser valid=True, after Submit /outlets/view/1747 ['Outlet is saved successfully'], Edit shows '('
 *
 * Preconditions:
 *     Setting default configuration=default (no company setting gates the CST No validation; after PR #10788 the rule allows letters, digits, '/', '-', '(', ')', '[', ']' and spaces for every company). User workflow "Edit Outlet" enabled. Admin user of the company under test (Staging Batleap) can log in on https://stagingbatleap.bizomstaging.in. Active retailer outlet {outletId} exists.
 *
 * Steps:
 *     1. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and enter '()[]' in the CST No field and click on Submit
 *     2. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and enter '(' in the CST No field and click on Submit
 *     3. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and check the CST No field under Tax Details
 *
 * Expected:
 *     1. User should be able to login to web and save the outlet with the message 'Outlet is saved successfully'
 *     2. User should be able to login to web and save the outlet with the message 'Outlet is saved successfully'
 *     3. User should be able to login to web and see CST No pre-filled with '('
 */
test.fixme('Verify CST No made only of brackets or a', tc(TICKET, 'TC_WEB_016'), async () => {
  // not automated yet - see tickets/PR1-T13616/cases.json
});

/**
 * TC_WEB_017 - Verify CST No with unbalanced or nested brackets is accepted (no bracket-pair check)
 *
 * Greybox: Pass on Execution_2026-10-13 (stagingbatleap)
 * Actual: Edit RETAILERS 1747 > Tax Details > Outlet Cst no: '((123]': browser valid=True, after Submit /outlets/view/1747 ['Outlet is saved successfully'], Edit shows '((123]'; '[(1256105-X)]': browser valid=True, after Submit /outlets/view/1747 ['Outlet is saved successfully'], Edit shows '[(1256105-X)]'
 *
 * Preconditions:
 *     Setting default configuration=default (no company setting gates the CST No validation; after PR #10788 the rule allows letters, digits, '/', '-', '(', ')', '[', ']' and spaces for every company). User workflow "Edit Outlet" enabled. Admin user of the company under test (Staging Batleap) can log in on https://stagingbatleap.bizomstaging.in. Active retailer outlet {outletId} exists.
 *
 * Steps:
 *     1. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and enter '((123]' in the CST No field and click on Submit
 *     2. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and enter '[(1256105-X)]' in the CST No field and click on Submit
 *
 * Expected:
 *     1. User should be able to login to web and save the outlet with the message 'Outlet is saved successfully'
 *     2. User should be able to login to web and save the outlet with the message 'Outlet is saved successfully'
 */
test.fixme('Verify CST No with unbalanced or nested brackets is', tc(TICKET, 'TC_WEB_017'), async () => {
  // not automated yet - see tickets/PR1-T13616/cases.json
});

/**
 * TC_WEB_018 - Verify a CST No made only of spaces is trimmed to empty and the outlet saves without error
 *
 * Greybox: Pass on Execution_2026-10-13 (stagingbatleap)
 * Actual: Edit RETAILERS 1747 > Tax Details > Outlet Cst no: '   ': browser valid=True, after Submit /outlets/view/1747 ['Outlet is saved successfully'], Edit shows ''
 *
 * Preconditions:
 *     Setting default configuration=default (no company setting gates the CST No validation; after PR #10788 the rule allows letters, digits, '/', '-', '(', ')', '[', ']' and spaces for every company). User workflow "Edit Outlet" enabled. Admin user of the company under test (Staging Batleap) can log in on https://stagingbatleap.bizomstaging.in. Active retailer outlet {outletId} exists. cst_no is not mandatory.
 *
 * Steps:
 *     1. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and enter '   ' (three spaces) in the CST No field
 *     2. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and click on Submit
 *     3. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and check the CST No field under Tax Details
 *
 * Expected:
 *     1. User should be able to login to web and enter the spaces in CST No
 *     2. User should be able to login to web and save the outlet with the message 'Outlet is saved successfully'
 *     3. User should be able to login to web and see the CST No field blank
 */
test.fixme('Verify a CST No made only of spaces is', tc(TICKET, 'TC_WEB_018'), async () => {
  // not automated yet - see tickets/PR1-T13616/cases.json
});

/**
 * TC_WEB_020 - Verify multiple consecutive inner spaces in CST No are kept as entered
 *
 * Greybox: Pass on Execution_2026-10-13 (stagingbatleap)
 * Actual: Edit RETAILERS 1747 > Tax Details > Outlet Cst no: 'ABC  (123)  [X]': browser valid=True, after Submit /outlets/view/1747 ['Outlet is saved successfully'], Edit shows 'ABC  (123)  [X]'
 *
 * Preconditions:
 *     Setting default configuration=default (no company setting gates the CST No validation; after PR #10788 the rule allows letters, digits, '/', '-', '(', ')', '[', ']' and spaces for every company). User workflow "Edit Outlet" enabled. Admin user of the company under test (Staging Batleap) can log in on https://stagingbatleap.bizomstaging.in. Active retailer outlet {outletId} exists.
 *
 * Steps:
 *     1. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and enter 'ABC  (123)  [X]' in the CST No field
 *     2. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and click on Submit
 *     3. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and check the CST No field under Tax Details
 *
 * Expected:
 *     1. User should be able to login to web and enter the value with double spaces
 *     2. User should be able to login to web and save the outlet with the message 'Outlet is saved successfully'
 *     3. User should be able to login to web and see CST No as 'ABC  (123)  [X]' with the double spaces kept
 */
test.fixme('Verify multiple consecutive inner spaces in CST No are', tc(TICKET, 'TC_WEB_020'), async () => {
  // not automated yet - see tickets/PR1-T13616/cases.json
});

/**
 * TC_WEB_021 - Verify a bracketed CST No is stored as entered in outlets.cstno and other Tax Details columns stay unchanged
 *
 * Greybox: Pass on Execution_2026-10-13 (stagingbatleap)
 * Actual: Edit RETAILERS 1747: Outlet Cst no '[MY] 201701041932 (1256105-X)' -> after Submit /outlets/view/1747 ['Outlet is saved successfully']; Edit shows '[MY] 201701041932 (1256105-X)'. Other Tax Details before {'OutletTaxno': '', 'OutletPanno': '', 'OutletCinno': '', 'OutletLicenseNo': ''} after {'Outlet
 *
 * Preconditions:
 *     Setting default configuration=default (no company setting gates the CST No validation; after PR #10788 the rule allows letters, digits, '/', '-', '(', ')', '[', ']' and spaces for every company). User workflow "Edit Outlet" enabled. Admin user of the company under test (Staging Batleap) can log in on https://stagingbatleap.bizomstaging.in. Active retailer outlet {outletId} has TIN/PAN/LBT/GSTIN values recorded before the test.
 *
 * Steps:
 *     1. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and check the Tax Details fields (TIN, PAN, LBT, GSTIN)
 *     2. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and enter '[MY] 201701041932 (1256105-X)' in the CST No field
 *     3. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and click on Submit
 *     4. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and check the Tax Details fields
 *
 * Expected:
 *     1. User should be able to login to web and note the current Tax Details values
 *     2. User should be able to login to web and enter the bracketed CST No
 *     3. User should be able to login to web and save the outlet with the message 'Outlet is saved successfully'
 *     4. User should be able to login to web and see CST No '[MY] 201701041932 (1256105-X)' and TIN, PAN, LBT and GSTIN unchanged
 */
test.fixme('Verify a bracketed CST No is stored as entered', tc(TICKET, 'TC_WEB_021'), async () => {
  // not automated yet - see tickets/PR1-T13616/cases.json
});

/**
 * TC_WEB_022 - Verify the outlet edit API (isJson) saves a CST No with brackets and returns success
 *
 * Greybox: Pass on Execution_2026-10-13 (stagingbatleap)
 * Actual: POST /outlets/edit/1747?isJson=1 with data[Outlet][cstno]='201701041932 (1256105-X)' (web session, isJson=1): HTTP 200 {'Result': 'true', 'Reason': 'RETAILERS Edited Successfully', 'outletid': '1747'}; Edit RETAILERS 1747 Outlet Cst no before '[MY] 201701041932 (1256105-X)', after '201701041932 (125
 *
 * Preconditions:
 *     Setting default configuration=default (no company setting gates the CST No validation; after PR #10788 the rule allows letters, digits, '/', '-', '(', ')', '[', ']' and spaces for every company). User workflow "Edit Outlet" enabled. Admin user of the company under test (Staging Batleap) has a valid API access_token {accessToken}. Use a dedicated active test outlet {outletId}, because a partial payload can reset dynamic properties.
 *
 * Steps:
 *     1. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and send the POST request from Test Data with cstno '201701041932 (1256105-X)'
 *     2. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and check the CST No field under Tax Details
 *
 * Expected:
 *     1. System should return HTTP 200 with JSON "Result":"true", "Reason":"<Outlet alias> Edited Successfully" and "outletid":"{outletId}"
 *     2. User should be able to login to web and see CST No pre-filled with '201701041932 (1256105-X)'
 */
test.fixme('Verify the outlet edit API isJson saves a CST', tc(TICKET, 'TC_WEB_022'), async () => {
  // not automated yet - see tickets/PR1-T13616/cases.json
});

/**
 * TC_WEB_023 - Verify the outlet edit API (isJson) rejects an invalid CST No with HTTP 400 and 'Invalid CST no.'
 *
 * Greybox: Pass on Execution_2026-10-13 (stagingbatleap)
 * Actual: POST /outlets/edit/1747?isJson=1 (admin web session + X-XSRF-TOKEN, no access_token) with data[Outlet][cstno]='<redacted>' -> rejected: JSON {"Result": false, "Reason": "Invalid CST no."}; Edit RETAILERS 1747 still shows Outlet Cst no '201701041932 (1256105-X)'. HTTP status is 200, not the 400 the s
 *
 * Preconditions:
 *     Setting default configuration=default (no company setting gates the CST No validation; after PR #10788 the rule allows letters, digits, '/', '-', '(', ')', '[', ']' and spaces for every company). User workflow "Edit Outlet" enabled. Admin user of the company under test (Staging Batleap) has a valid API access_token {accessToken}. Active test outlet {outletId} has CST No '201701041932 (1256105-X)'.
 *
 * Steps:
 *     1. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and send the POST request from Test Data with cstno '<redacted>'
 *     2. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/edit/{outletId} and check the CST No field under Tax Details
 *
 * Expected:
 *     1. System should return HTTP 400 with JSON {"Result":false,"Reason":"Invalid CST no."}
 *     2. User should be able to login to web and see CST No still '201701041932 (1256105-X)'
 */
test.fixme('Verify the outlet edit API isJson rejects an invalid', tc(TICKET, 'TC_WEB_023'), async () => {
  // not automated yet - see tickets/PR1-T13616/cases.json
});

/**
 * TC_WEB_024 - Verify the outlet add API (isJson) accepts a bracketed CST No and rejects an invalid one
 *
 * Greybox: Pass on Execution_2026-10-13 (stagingbatleap)
 * Actual: POST /outlets/add?isJson=1 (web session): request 1 cstno '201701041932 (1256105-X)' -> HTTP 200 {'Result': 'true', 'Response': 'The outlet id 1748 has been saved', 'outletid': '1748'}, new outlet Edit shows Outlet Cst no '201701041932 (1256105-X)'; request 2 cstno '<redacted>' -> HTTP 200 {'Result'
 *
 * Preconditions:
 *     Setting default configuration=default (no company setting gates the CST No validation; after PR #10788 the rule allows letters, digits, '/', '-', '(', ')', '[', ']' and spaces for every company). Admin user of the company under test (Staging Batleap) has a valid API access_token {accessToken}. Active beat {beatId} and area {areaId} exist. Transaction ids {txnId1} and {txnId2} are unused.
 *
 * Steps:
 *     1. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/add and send the first POST request from Test Data with cstno '201701041932 (1256105-X)'
 *     2. Login to web as Admin and go to https://stagingbatleap.bizomstaging.in/outlets/add and send the second POST request from Test Data with cstno '<redacted>'
 *
 * Expected:
 *     1. System should return JSON with "Result":"true", "Response":"The outlet id {newOutletId} has been saved" and "outletid":"{newOutletId}"
 *     2. System should return JSON {"Result":false,"Reason":"Invalid CST no."} and not create the outlet
 */
test.fixme('Verify the outlet add API isJson accepts a bracketed', tc(TICKET, 'TC_WEB_024'), async () => {
  // not automated yet - see tickets/PR1-T13616/cases.json
});
