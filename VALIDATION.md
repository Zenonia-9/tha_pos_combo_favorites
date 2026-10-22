# Native combo export/import validation

Validated locally on 2026-10-22 against `THA17`, addon version `17.0.1.0.15`.

## Passed

- Python compilation, manifest parsing, XML parsing (three files), JavaScript syntax (two assets), and `git diff --check`.
- Named addon upgrade with the test command in README: **16 tests, 0 failures, 0 errors**.
- Native product export/import round trips using names, External IDs, and Database IDs for supported native export fields; product and availability IDs remain unchanged.
- Actual native XLSX generation through `ExcelExport.from_data`, followed by `base_import.import.execute_import`.
- Scoped option names, comma-separated options, reordered columns, vertical continuation rows, and exported availability references without a Combo Choice column.
- Continuation isolation between products; missing/ambiguous names and invalid option membership rejected, including explicit ID references.
- Product/combo pair updates retain omitted choices and restrictions in omitted columns. Explicit blank option cells restore all configured options after continuation merging.
- Nested row inference in either input order, native root `combo_ids` synchronization, and nested restrictions in the JSON used by POS.
- Exported availability references cannot reassign another product's rows.
- Installed `tha_product_attribute_import` converter still resolves duplicate attribute-value names and continuation rows correctly.
- Odoo restarted after upgrade; Compose services healthy and `/web/health` returned HTTP 200.

Test fixtures are transactional and rolled back. Only `tha_pos_combo_favorites` was upgraded.

## Boundaries

Chrome UI validation could not finish: the existing tab reported `Debugger unattached`; opening a fresh local tab timed out waiting for `Page.navigate`. Export/import controller and ORM behavior were exercised by the tests above; the rendered export/import dialogs and POS interaction were not verified in this run.

Native Odoo 17 exports display names for many-to-many Database ID columns. Use option-name or External ID columns for native export round trips; numeric Database IDs are supported on import and covered by tests.
