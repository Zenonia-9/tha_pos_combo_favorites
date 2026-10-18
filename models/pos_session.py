from odoo import models


class PosSession(models.Model):
    _inherit = "pos.session"

    def _loader_params_pos_combo(self):
        params = super()._loader_params_pos_combo()
        products = self._context.get("loaded_data", {}).get("product.product", [])
        combo_ids = set().union(*(product.get("combo_ids", []) for product in products)) if products else set()
        combos = self.env["pos.combo"].browse(combo_ids).exists()
        while combos:
            child_ids = set(combos.mapped("tha_child_combo_ids").ids) - combo_ids
            if not child_ids:
                break
            combo_ids.update(child_ids)
            combos = self.env["pos.combo"].browse(child_ids)
        params["ids"] = combo_ids
        params["search_params"]["fields"] = [
            "id", "name", "combo_line_ids", "base_price",
            "tha_child_combo_ids", "tha_max_selection",
        ]
        return params

    def _loader_params_product_product(self):
        params = super()._loader_params_product_product()
        product_fields = params["search_params"]["fields"]
        if "tha_is_favorite" not in product_fields:
            product_fields.append("tha_is_favorite")
        return params
