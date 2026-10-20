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

## Excel import

Open **Point of Sale → Products → Combo Set Availability**. Click **Excel Template** to download `static/templates/combo_set_availability.xlsx`. Fill its **Import** sheet, then use the list's **Import records** action. The **Examples and Guide** sheet is explanatory and should not be imported.

Use one row per combo set product and Combo Choice:

| Combo Set Product | Combo Choice | Products | Sub Choices |
| --- | --- | --- | --- |
| Set A | Meal | Chicken,Fish Cake,Pork | |
| Set B | Meal | Chicken,Pork | |
| Set B | Drinks | | Soft Drinks,Juice |
| Set B | Soft Drinks | Coke | |

- Separate multiple options in one cell with commas. Every option must already exist in the selected shared Combo Choice. Products are product variants; Combo Set Product identifies the product template.
- Both blank option cells mean all products and all sub choices. A blank cell also resets an existing restricted list to all its source options during an update.
- An imported existing product/combo pair updates in place, so an availability row External ID is optional. Include all main-choice rows before nested override rows when assigning combos to a new set. Importing a choice outside the set's current tree adds it as a main choice.
- Names must identify existing records uniquely. For duplicate names or names containing commas, export and import **External ID** or **Database ID** fields instead. Examples: `product_tmpl_id/id`, `combo_id/id`, `product_ids/id`, `child_combo_ids/id` for external IDs; replace `/id` with `/.id` for numeric database IDs. Multiple IDs in Products or Sub Choices remain comma-separated.
- POS managers can edit/import availability. POS users can read the resulting rules. Availability follows the combo set product's company access.
