from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env["product.template"].with_context(active_test=False).search([
        ("combo_ids", "!=", False),
    ]).tha_sync_combo_availability()
