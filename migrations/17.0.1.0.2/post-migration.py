from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    nested_combos = env["pos.combo"].search([]).filtered(
        lambda combo: combo.tha_child_combo_ids and not combo.combo_line_ids
    )
    nested_combos.write({"tha_choice_type": "subchoices"})
