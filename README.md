# POS Combo Sets and Favorites

Odoo 17 addon extending Point of Sale with nested combo choices and a Favorites product category.

## Features

- Nest combo choices to any depth, such as Drinks → Beer → available beer products.
- Set the maximum number of selections allowed for each group; at least one selection is required.
- Keep selected leaf products in Odoo's standard POS combo order-line flow.
- Choose different available products and sub choices for each combo set product.
- Add a Star category beside Home that filters to products marked **Favorite** in the product catalog.

## Setup

1. Install `tha_pos_combo_favorites` with `point_of_sale` installed.
2. Open **Point of Sale → Products → Combo Choices**.
3. Create a group, add product options in the Products in Combo list, and select any existing nested groups in **Sub Choices**.
4. Set **Maximum Selections** to limit the combined number of direct products and nested groups the customer may choose from this group.
5. Configure each selected nested group with its own products, nested groups, and selection limit.
6. Open a combo set product's **Combo Choices** tab and click **Add a line**. Select a Combo Choice; its Products and Sub Choices appear as removable tags, like attribute Values.
7. Remove options unavailable for this set, then save. Nested choices appear as additional rows after saving, so their products can also be restricted for this set.

Products and nested groups can coexist. Sub Choices only selects existing groups; it does not create groups. Removing a parent relationship does not delete its nested groups.

Nested choices open in their own configurator popup. A maximum of one behaves like a radio selection: choosing a different option replaces the previous one. On upgrade to 17.0.1.0.3, existing nested relationships are migrated and retained.

Confirming a nested popup completes that choice in the parent popup. The parent shows the category name separately from a labeled product badge, such as “Juices” and “Selected product: Lychee.” Click a selected category to choose again; canceling keeps the saved choice. Groups allowing multiple selections also provide a Remove button for selected categories.

The technical addon directory and module ID are `tha_pos_combo_favorites`. Its display name is **POS Combo Sets and Favorites**.

## Availability for each set

Each product and Combo Choice pair has its own availability record. Editing its tags changes only that set. The shared Combo Choice keeps its original products, nested choices, prices, and selection limit. Main rows determine the product's native Odoo `combo_ids`; nested rows only configure that product's nested popups.

Blank Products means all direct products in that Combo Choice. Blank Sub Choices means all child choices in it. This applies when creating records, editing them, and importing new or existing rows. Clearing every tag restores all options when saved. An option type with no source options remains empty.

Saved non-empty lists are explicit selections. When a shared Combo Choice later gains new options, clear the relevant list and save to include all current options again. Removing a main choice row removes that assignment from the set. Removing a nested availability row resets it to its default options when saved; remove the child tag in its parent row to hide that branch.

Upgrade 17.0.1.0.14 preserves existing main assignments and creates availability rows for their complete choice trees, initially allowing all existing options. Existing order lines retain their original combo item references. Reload POS after changing availability.

## Standard product export and import

Use **Point of Sale → Products → Products** in list view. Select the combo set products, choose Odoo's normal **Export** action, and enable **I want to update data (import-compatible export)**. Select:

- **External ID** and **Name**.
- **Combo Choices / Combo Choice**.
- **Combo Choices / Products**.
- **Combo Choices / Sub Choices**.

Export XLSX or CSV, edit it, then use the Products list's normal **Import records** action. Keep the product External IDs when updating existing products; importing only a product name follows Odoo's normal new-product behavior. When creating new combo set products, also map **Product Type** (`detailed_type`) to **Combo**. The technical relation remains `tha_combo_availability_ids`; its export label is now **Combo Choices**.

Comma-separated options and one-option-per-row layouts are supported:

| External ID | Name | Combo Choices / Combo Choice | Combo Choices / Products | Combo Choices / Sub Choices |
| --- | --- | --- | --- | --- |
| set_a | Set A | Meal | Chicken | |
| | | | Pork | |
| | | Drinks | | Soft Drinks,Juice |
| | | Soft Drinks | Coke | |
| set_b | Set B | Meal | Chicken,Pork | |

The first two rows form one Meal choice containing Chicken and Pork. Blank product fields continue the same product. A blank Combo Choice with option values continues the preceding choice within that product. Start each product with its own Combo Choice; continuation never carries a choice across products. Products and Sub Choices can each span continuation rows. Spaces around comma-separated options are ignored.

After continuation rows have been combined, a blank **Products** cell means all direct products, and a blank **Sub Choices** cell means all child choices. This also resets existing restrictions when updating. An option column that is not imported preserves its existing value. Existing choices omitted from the file remain assigned to the set.

Products are matched within the selected Combo Choice's direct products; Sub Choices are matched within its configured children. Duplicate names elsewhere do not affect matching. Missing options, duplicate names within that choice, and ambiguous Combo Choice names stop the import with a clear error. Shared choices and options must already exist; imports select them rather than creating new definitions. Exported product labels containing internal references, such as `[RM-0011] 7-up`, are supported.

Nested choice rows are inferred from the shared hierarchy even when they appear before their parent in the file. Importing both Drinks and Soft Drinks configures Soft Drinks as a nested choice when it belongs under Drinks. Existing main choices remain assigned. Exported **Main Choice** flags can preserve deliberately overlapping main assignments.

Use **External ID** or **Database ID** relation subfields when names are ambiguous or contain commas. Technical examples are `tha_combo_availability_ids/combo_id/id`, `tha_combo_availability_ids/product_ids/id`, and `tha_combo_availability_ids/child_combo_ids/id`; replace `/id` with `/.id` for database IDs. The availability row's own `tha_combo_availability_ids/id` is optional: imports also update existing rows by product/choice pair. A referenced availability row cannot be moved to another product; remove its row ID when creating a different product.

For native many-to-many exports, use the Products and Sub Choices name columns or their External ID subfields. Odoo 17 exports display names for many-to-many Database ID columns; numeric Database IDs remain supported when supplied during import.

The **Combo Set Availability** screen remains available as an overview and uses normal Odoo export/import actions too. POS managers can edit/import availability; POS users can read rules under the set product's company access. The converter cooperates with `tha_product_attribute_import` when that addon is installed, without requiring it as a dependency.

## Validation

The regression suite covers native product `load()`, scoped names and IDs, continuation rows, omitted choices, blank defaults, nested inference, availability ownership, native export round trips, and the actual Odoo XLSX export/import pipeline. Compatibility with `tha_product_attribute_import` is checked when installed. Test records are rolled back.

```powershell
docker compose stop gateway_17 odoo_17
docker compose run --rm --no-deps odoo_17 odoo -c /run/odoo/odoo.conf -d THA17 -u tha_pos_combo_favorites --stop-after-init --no-http --workers=0 --max-cron-threads=0 --test-enable --test-tags /tha_pos_combo_favorites
docker compose up -d --wait
docker compose restart odoo_17
```
