from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PosCombo(models.Model):
    _inherit = "pos.combo"

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
