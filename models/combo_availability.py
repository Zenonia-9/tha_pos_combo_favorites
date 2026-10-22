from odoo import api, fields, models, Command, _
from odoo.exceptions import ValidationError


class PosComboAvailability(models.Model):
    _name = "pos.combo.availability"
    _description = "Combo Set Availability"
    _rec_name = "combo_id"
    _order = "product_tmpl_id, id"

    product_tmpl_id = fields.Many2one(
        "product.template", string="Combo Set Product", required=True,
        ondelete="cascade", index=True,
    )
    combo_id = fields.Many2one(
        "pos.combo", string="Combo Choice", required=True, ondelete="cascade", index=True,
    )
    is_root = fields.Boolean(string="Main Choice", default=True)
    product_ids = fields.Many2many(
        "product.product", "tha_combo_availability_product_rel", "availability_id", "product_id",
        string="Products", help="Allowed products for this set. Blank means all products in this choice.",
    )
    child_combo_ids = fields.Many2many(
        "pos.combo", "tha_combo_availability_child_rel", "availability_id", "combo_id",
        string="Sub Choices", help="Allowed sub choices for this set. Blank means all sub choices.",
    )
    source_product_ids = fields.Many2many("product.product", compute="_compute_source_options")
    source_child_combo_ids = fields.Many2many(
        related="combo_id.tha_child_combo_ids", string="Configured Sub Choices",
    )

    _sql_constraints = [
        ("product_combo_unique", "unique(product_tmpl_id, combo_id)",
         "Each combo choice can only have one availability row per set."),
    ]

    @api.depends("combo_id.combo_line_ids.product_id")
    def _compute_source_options(self):
        for record in self:
            record.source_product_ids = record.combo_id.combo_line_ids.product_id

    @api.onchange("combo_id")
    def _onchange_combo_id(self):
        for record in self:
            record.product_ids = record.combo_id.combo_line_ids.product_id
            record.child_combo_ids = record.combo_id.tha_child_combo_ids

    @api.constrains("product_tmpl_id", "combo_id", "product_ids", "child_combo_ids")
    def _check_available_options(self):
        for record in self:
            if record.product_tmpl_id.detailed_type != "combo":
                raise ValidationError(_("Availability can only be configured for a combo set product."))
            if record.product_ids - record.combo_id.combo_line_ids.product_id:
                raise ValidationError(_("Products must belong to the selected Combo Choice: %s", record.combo_id.display_name))
            if record.child_combo_ids - record.combo_id.tha_child_combo_ids:
                raise ValidationError(_("Sub Choices must belong to the selected Combo Choice: %s", record.combo_id.display_name))

    def _fill_blank_options(self):
        for record in self:
            values = {}
            if not record.product_ids:
                values["product_ids"] = [Command.set(record.combo_id.combo_line_ids.product_id.ids)]
            if not record.child_combo_ids:
                values["child_combo_ids"] = [Command.set(record.combo_id.tha_child_combo_ids.ids)]
            if values:
                super(PosComboAvailability, record).write(values)

    def _attach_to_products(self):
        for product in self.product_tmpl_id:
            tree = product.tha_get_combo_tree()
            extra = self.filtered(lambda record: record.product_tmpl_id == product).combo_id - tree
            nested = self.env["pos.combo"]
            for combo in extra:
                nested |= product.tha_get_combo_tree(combo) - combo
            roots = extra - nested
            if roots:
                product.with_context(tha_skip_combo_sync=True).write({
                    "combo_ids": [Command.link(combo.id) for combo in roots],
                })
            product.tha_sync_combo_availability()

    @api.model_create_multi
    def create(self, values_list):
        if self.env.context.get("import_file"):
            records = self.browse()
            seen = set()
            for values in values_list:
                pair = (values.get("product_tmpl_id"), values.get("combo_id"))
                if pair in seen:
                    raise ValidationError(_("Use one Excel row per combo set product and Combo Choice."))
                seen.add(pair)
                existing = self.search([
                    ("product_tmpl_id", "=", values.get("product_tmpl_id")),
                    ("combo_id", "=", values.get("combo_id")),
                ], limit=1)
                if existing:
                    existing.with_context(tha_skip_combo_sync=True).write(values)
                    records |= existing
                else:
                    records |= super().create([values])
        else:
            records = super().create(values_list)
        records._fill_blank_options()
        if not self.env.context.get("tha_skip_combo_sync"):
            records._attach_to_products()
        return records

    def write(self, values):
        if self.env.context.get("import_file") and "product_tmpl_id" in values:
            if any(record.product_tmpl_id.id != values["product_tmpl_id"] for record in self):
                raise ValidationError(_("An exported combo availability row cannot be moved to another product. Remove its row ID to create a new assignment."))
        result = super().write(values)
        if not result:
            return result
        self._fill_blank_options()
        if not self.env.context.get("tha_skip_combo_sync"):
            self._attach_to_products()
        return True

    def unlink(self):
        if self.env.context.get("tha_skip_combo_sync"):
            return super().unlink()
        products = self.product_tmpl_id
        roots_by_product = {
            product.id: self.filtered(
                lambda record: record.product_tmpl_id == product and record.is_root
            ).combo_id.ids
            for product in products
        }
        result = super().unlink()
        for product in products:
            product.with_context(tha_skip_combo_sync=True).write({
                "combo_ids": [Command.unlink(combo_id) for combo_id in roots_by_product[product.id]],
            })
        products.tha_sync_combo_availability()
        return result
