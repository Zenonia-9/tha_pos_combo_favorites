# POS Nested Combo Sets

Odoo 17 addon extending Point of Sale combo choices with nested sub choices and a selection limit per group.

## Features

- Nest combo choices to any depth, such as Drinks → Beer → available beer products.
- Set the maximum number of selections allowed for each group; at least one selection is required.
- Keep selected leaf products in Odoo's standard POS combo order-line flow.

## Setup

1. Install `tha_pos_combo_set` with `point_of_sale` installed.
2. Open **Point of Sale → Products → Combo Choices**.
3. Create a group, choose **Products** or **Sub Choices** under **Choice Contents**, and set **Maximum Selections**.
4. For a product group, add products in the Products in Combo list.
5. For a nested group, choose **Sub Choices** and add child choices. Open each child choice to select its parent and configure its own contents.
6. Assign top-level groups to the combo product as usual.

A group should contain either product lines or sub choices, not both. Configure nested groups with a maximum of one when the customer must choose one category or item.

On upgrade to 17.0.1.0.2, existing groups that already contain child choices are switched to **Sub Choices** automatically.
