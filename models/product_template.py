from odoo import api, fields, models, Command


class ProductTemplate(models.Model):
    _inherit = "product.template"

    tha_combo_availability_ids = fields.One2many(
        "pos.combo.availability", "product_tmpl_id", string="Availability for This Set", copy=True,
    )
    tha_combo_availability = fields.Json(compute="tha_compute_combo_availability")

    @api.depends(
        "tha_combo_availability_ids.combo_id",
        "tha_combo_availability_ids.product_ids",
        "tha_combo_availability_ids.child_combo_ids",
        "tha_combo_availability_ids.combo_id.combo_line_ids.product_id",
        "tha_combo_availability_ids.combo_id.tha_child_combo_ids",
    )
    def tha_compute_combo_availability(self):
        for product in self:
            product.tha_combo_availability = {
                str(record.combo_id.id): {
                    "product_ids": (record.product_ids or record.combo_id.combo_line_ids.product_id).ids,
                    "child_combo_ids": (record.child_combo_ids or record.combo_id.tha_child_combo_ids).ids,
                }
                for record in product.tha_combo_availability_ids
            }

    def tha_get_combo_tree(self, roots=None):
        self.ensure_one()
        pending = self.combo_ids if roots is None else roots
        combos = self.env["pos.combo"]
        while pending:
            combos |= pending
            pending = pending.tha_child_combo_ids - combos
        return combos

    def tha_sync_combo_availability(self):
        availability = self.env["pos.combo.availability"].with_context(
            tha_skip_combo_sync=True, import_file=False,
        )
        for product in self:
            combos = product.tha_get_combo_tree()
            records = product.tha_combo_availability_ids
            stale = records.filtered(lambda record: record.combo_id not in combos)
            records -= stale
            stale.with_context(
                tha_skip_combo_sync=True,
            ).unlink()
            for record in records:
                is_root = record.combo_id in product.combo_ids
                if record.is_root != is_root:
                    record.with_context(tha_skip_combo_sync=True).write({"is_root": is_root})
            missing = combos - records.combo_id
            if missing:
                availability.create([
                    {"product_tmpl_id": product.id, "combo_id": combo.id,
                     "is_root": combo in product.combo_ids}
                    for combo in missing
                ])
        return True

    @api.onchange("tha_combo_availability_ids")
    def tha_onchange_combo_availability(self):
        for product in self:
            product.combo_ids = product.tha_combo_availability_ids.filtered("is_root").combo_id

    @api.model_create_multi
    def create(self, values_list):
        if self.env.context.get("tha_skip_combo_sync"):
            return super().create(values_list)
        products = super(ProductTemplate, self.with_context(tha_skip_combo_sync=True)).create(values_list)
        for product, values in zip(products, values_list):
            if "tha_combo_availability_ids" in values and "combo_ids" not in values:
                product.write({"combo_ids": [Command.set(product.tha_combo_availability_ids.filtered("is_root").combo_id.ids)]})
        products.filtered("combo_ids").tha_sync_combo_availability()
        return products.with_env(self.env)

    def write(self, values):
        if self.env.context.get("tha_skip_combo_sync"):
            return super().write(values)
        result = super(ProductTemplate, self.with_context(tha_skip_combo_sync=True)).write(values)
        if "tha_combo_availability_ids" in values and "combo_ids" not in values:
            for product in self:
                product.with_context(tha_skip_combo_sync=True).write({
                    "combo_ids": [Command.set(product.tha_combo_availability_ids.filtered("is_root").combo_id.ids)],
                })
        if "combo_ids" in values or "tha_combo_availability_ids" in values:
            self.tha_sync_combo_availability()
        return result
