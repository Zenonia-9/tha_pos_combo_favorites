from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PosCombo(models.Model):
    _inherit = "pos.combo"

    def write(self, values):
        result = super().write(values)
        if "combo_line_ids" in values or "tha_child_combo_ids" in values:
            records = self.env["pos.combo.availability"].search([("combo_id", "in", self.ids)])
            for record in records:
                products = record.product_ids & record.combo_id.combo_line_ids.product_id
                children = record.child_combo_ids & record.combo_id.tha_child_combo_ids
                if products != record.product_ids or children != record.child_combo_ids:
                    record.with_context(tha_skip_combo_sync=True).write({
                        "product_ids": [fields.Command.set(products.ids)],
                        "child_combo_ids": [fields.Command.set(children.ids)],
                    })
            records.product_tmpl_id.tha_sync_combo_availability()
        return result

    def unlink(self):
        products = self.env["product.template"].with_context(active_test=False).search([
            "|", ("combo_ids", "in", self.ids), ("tha_combo_availability_ids.combo_id", "in", self.ids),
        ])
        result = super().unlink()
        products.tha_sync_combo_availability()
        return result

    tha_parent_combo_id = fields.Many2one(
        "pos.combo", string="Legacy Parent Choice", ondelete="set null", index=True
    )
    tha_choice_type = fields.Selection(
        [("products", "Products"), ("subchoices", "Sub Choices")],
        string="Legacy Choice Contents", default="products", required=True,
    )
    tha_child_combo_ids = fields.Many2many(
        "pos.combo", "pos_combo_choice_rel", "parent_id", "child_id",
        string="Sub Choices",
    )
    tha_parent_combo_ids = fields.Many2many(
        "pos.combo", "pos_combo_choice_rel", "child_id", "parent_id",
        string="Parent Choices",
    )
    tha_max_selection = fields.Integer(
        string="Maximum Selections",
        default=1,
        required=True,
        help="Maximum number of products or sub choices the customer can select. At least one is required.",
    )

    @api.constrains("combo_line_ids", "tha_child_combo_ids")
    def _check_combo_line_ids_is_not_null(self):
        # Override the native non-empty check: a parent may offer direct products,
        # child combo choices, or both.
        return

    @api.constrains("tha_max_selection")
    def _check_tha_max_selection(self):
        if any(combo.tha_max_selection < 1 for combo in self):
            raise ValidationError(_("Maximum Selections must be at least one."))

    @api.constrains("tha_child_combo_ids")
    def _check_tha_combo_hierarchy(self):
        for combo in self:
            seen = set()
            stack = list(combo.tha_child_combo_ids)
            while stack:
                child = stack.pop()
                if child == combo:
                    raise ValidationError(_("A combo choice cannot contain itself."))
                if child.id not in seen:
                    seen.add(child.id)
                    stack.extend(child.tha_child_combo_ids)
                if len(child.tha_parent_combo_ids) > 1:
                    raise ValidationError(_("A sub choice can only belong to one parent choice."))
