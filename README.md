# POS Nested Combo Sets

Odoo 17 addon extending Point of Sale combo choices with nested sub choices and a selection limit per group.

## Features

- Nest combo choices to any depth, such as Drinks → Beer → available beer products.
- Set the maximum number of selections allowed for each group; at least one selection is required.
- Keep selected leaf products in Odoo's standard POS combo order-line flow.

## Setup

1. Install `tha_pos_combo_set` with `point_of_sale` installed.
2. Open **Point of Sale → Products → Combo Choices**.
3. Create a group, add product options in the Products in Combo list, and select any existing nested groups in **Sub Choices**.
4. Set **Maximum Selections** to limit the combined number of direct products and nested groups the customer may choose from this group.
5. Configure each selected nested group with its own products, nested groups, and selection limit.
6. Assign top-level groups to the combo product as usual.

Products and nested groups can coexist. Sub Choices only selects existing groups; it does not create groups. Removing a parent relationship does not delete its nested groups.

Nested choices open in their own configurator popup. A maximum of one behaves like a radio selection: choosing a different option replaces the previous one. On upgrade to 17.0.1.0.3, existing nested relationships are migrated and retained.
