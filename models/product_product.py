from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    tha_is_favorite = fields.Boolean(
        string="POS Favorite",
        compute="_compute_tha_is_favorite",
    )

    @api.depends("product_tmpl_id.priority")
    def _compute_tha_is_favorite(self):
        for product in self:
            product.tha_is_favorite = product.product_tmpl_id.priority == "1"
