from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PosCombo(models.Model):
    _inherit = "pos.combo"

    tha_parent_combo_id = fields.Many2one(
        "pos.combo", string="Parent Choice", ondelete="cascade", index=True
    )
    tha_child_combo_ids = fields.One2many(
        "pos.combo", "tha_parent_combo_id", string="Sub Choices"
    )
    tha_max_selection = fields.Integer(
        string="Maximum Selections",
        default=1,
        required=True,
        help="Maximum number of products or sub choices the customer can select. At least one is required.",
    )

    @api.constrains("combo_line_ids", "tha_child_combo_ids")
    def _check_combo_line_ids_is_not_null(self):
        for combo in self:
            if bool(combo.combo_line_ids) == bool(combo.tha_child_combo_ids):
                raise ValidationError(
                    _("A combo choice must contain either products or sub choices, but not both.")
                )

    @api.constrains("tha_max_selection")
    def _check_tha_max_selection(self):
        if any(combo.tha_max_selection < 1 for combo in self):
            raise ValidationError(_("Maximum Selections must be at least one."))

    @api.constrains("tha_parent_combo_id")
    def _check_tha_combo_hierarchy(self):
        for combo in self:
            ancestor = combo.tha_parent_combo_id
            seen = {combo.id}
            while ancestor:
                if ancestor.id in seen:
                    raise ValidationError(_("A combo choice cannot contain itself."))
                seen.add(ancestor.id)
                ancestor = ancestor.tha_parent_combo_id


class PosComboLine(models.Model):
    _inherit = "pos.combo.line"

    @api.constrains("combo_id")
    def _check_tha_combo_line_is_leaf(self):
        for line in self:
            if line.combo_id.tha_child_combo_ids:
                raise ValidationError(
                    _("A combo choice cannot contain products and sub choices at the same time.")
                )
