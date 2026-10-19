# PR1-T13616

Greybox folder: `PR1-T13616_BAT_Genesis_Support_special_characters` - runs: Execution_2026-10-13 - company: stagingbatleap

Exported 24 verified case(s): 24 web

| Case | Surface | Greybox | Defect | Title |
|---|---|---|---|---|
| TC_WEB_001 | web | Pass |  | Verify Admin can save a Malaysian business registration number with parentheses in CST No  |
| TC_WEB_002 | web | Pass |  | Verify CST No with square brackets, parentheses and spaces together is saved on Edit Outle |
| TC_WEB_003 | web | Pass |  | Verify Admin can create an outlet with a CST No containing slash, hyphen, parentheses, squ |
| TC_WEB_004 | web | Pass |  | Verify other outlet details can be edited and saved when the stored CST No already contain |
| TC_WEB_005 | web | Pass |  | Verify the ticket's sample registration number with a leading space, inner spaces and lowe |
| TC_WEB_006 | web | Pass |  | Verify CST No formats that were valid before the change (alphanumeric, slash, hyphen) stil |
| TC_WEB_007 | web | Pass |  | Verify CST No can be cleared and the outlet saves when the field is not mandatory |
| TC_WEB_008 | web | Pass |  | Verify Edit Outlet rejects a CST No containing '@' with the message 'Invalid CST no.' |
| TC_WEB_009 | web | Pass |  | Verify Edit Outlet rejects CST No values with special characters other than / - ( ) [ ] an |
| TC_WEB_010 | web | Pass |  | Verify Add Outlet blocks an invalid CST No in a collapsed Tax Details section and opens th |
| TC_WEB_011 | web | Pass |  | Verify Add Outlet browser validation blocks an apostrophe and '#' in CST No |
| TC_WEB_012 | web | Pass |  | Verify HTML/script injection in CST No is rejected on Edit Outlet and never executes |
| TC_WEB_013 | web | Pass |  | Verify full-width (Unicode) brackets and accented letters in CST No are rejected on Edit O |
| TC_WEB_014 | web | Pass |  | Verify the LBT No field still rejects brackets because the change applies to CST No only |
| TC_WEB_015 | web | Pass |  | Verify CST No values that start or end with a bracket, slash or hyphen are accepted |
| TC_WEB_016 | web | Pass |  | Verify CST No made only of brackets or a single bracket is accepted as the new rule allows |
| TC_WEB_017 | web | Pass |  | Verify CST No with unbalanced or nested brackets is accepted (no bracket-pair check) |
| TC_WEB_018 | web | Pass |  | Verify a CST No made only of spaces is trimmed to empty and the outlet saves without error |
| TC_WEB_019 | web | Fail | DEF-CST-01 | Verify a 255-character CST No made of allowed characters is saved in full |
| TC_WEB_020 | web | Pass |  | Verify multiple consecutive inner spaces in CST No are kept as entered |
| TC_WEB_021 | web | Pass |  | Verify a bracketed CST No is stored as entered in outlets.cstno and other Tax Details colu |
| TC_WEB_022 | web | Pass |  | Verify the outlet edit API (isJson) saves a CST No with brackets and returns success |
| TC_WEB_023 | web | Pass |  | Verify the outlet edit API (isJson) rejects an invalid CST No with HTTP 400 and 'Invalid C |
| TC_WEB_024 | web | Pass |  | Verify the outlet add API (isJson) accepts a bracketed CST No and rejects an invalid one |
