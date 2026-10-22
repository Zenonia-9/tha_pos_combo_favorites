from odoo import api, models, _


class IrFieldsConverter(models.AbstractModel):
    _inherit = "ir.fields.converter"

    @api.model
    def _str_to_one2many(self, model, field, records):
        if field.comodel_name == "pos.combo.availability":
            records = self.tha_complete_combo_references(model, field, records)
            records = self.tha_merge_combo_option_rows(records)
        return super()._str_to_one2many(model, field, records)

    @api.model
    def tha_merge_combo_option_rows(self, records):
        merged = []
        option_fields = {"product_ids", "child_combo_ids"}
        for record in records:
            previous = merged[-1] if merged else {}
            if (
                not record.get("combo_id")
                and {name for name, value in record.items() if value} <= option_fields | {"combo_id"}
                and previous.get("combo_id")
                and any(record.get(name) for name in option_fields)
            ):
                combined = dict(previous)
                for name in option_fields:
                    values = record.get(name)
                    if not values:
                        continue
                    previous_values = combined.get(name)
                    if not previous_values:
                        combined[name] = values
                        continue
                    if (
                        len(values) != 1 or len(previous_values) != 1
                        or len(values[0]) != 1 or set(values[0]) != set(previous_values[0])
                        or next(iter(values[0])) not in (None, "id", ".id")
                    ):
                        raise ValueError(_("Use the same option reference column in combo continuation rows."))
                    reference = next(iter(values[0]))
                    combined[name] = [{reference: ",".join(filter(None, [
                        previous_values[0][reference], values[0][reference],
                    ]))}]
                merged[-1] = combined
            else:
                merged.append(record)
        return merged

    @api.model
    def tha_complete_combo_references(self, model, field, records):
        completed = []
        for record in records:
            if not record.get("combo_id") and (record.get("id") or record.get(".id")):
                reference = "id" if record.get("id") else ".id"
                record_id, _, warnings = self.db_id_for(model, field, reference, record[reference])
                if record_id and not warnings:
                    availability = self.env["pos.combo.availability"].browse(record_id)
                    record = dict(record, combo_id=[{".id": str(availability.combo_id.id)}])
            completed.append(record)
        return completed

    @api.model
    def for_model(self, model, fromtype=str):
        convert = super().for_model(model, fromtype=fromtype)
        if model._name != "pos.combo.availability" or fromtype is not str:
            return convert

        def convert_combo_availability(record, log):
            try:
                record = self.tha_scope_combo_options(model, record)
            except ValueError as error:
                log("combo_id", error)
                return {}
            return convert(record, log)

        return convert_combo_availability

    @api.model
    def tha_scope_combo_options(self, model, record):
        choices = record.get("combo_id")
        if not choices:
            if record.get("product_ids") or record.get("child_combo_ids"):
                raise ValueError(_("A Combo Choice is required before its Products or Sub Choices."))
            return record
        combo_id, warnings = self._str_to_many2one(model, model._fields["combo_id"], choices)
        if warnings:
            raise ValueError(_("The Combo Choice reference is ambiguous. Use a unique name, External ID or Database ID."))
        if not combo_id:
            raise ValueError(_("A Combo Choice is required before its options."))
        combo = self.env["pos.combo"].browse(combo_id)
        scoped = dict(record, combo_id=[{".id": str(combo_id)}])
        sources = {
            "product_ids": combo.combo_line_ids.product_id,
            "child_combo_ids": combo.tha_child_combo_ids,
        }
        for field_name, candidates in sources.items():
            values = record.get(field_name)
            if not values or len(values) != 1 or set(values[0]) != {None} or not values[0][None]:
                continue
            self.env.context.get("import_flush", lambda **kwargs: None)(model=candidates._name)
            identifiers = []
            for name in values[0][None].split(","):
                name = name.strip()
                matches = candidates.with_context(active_test=False).name_search(
                    name, [("id", "in", candidates.ids)], operator="=", limit=2,
                ) if name else []
                if len(matches) != 1:
                    raise ValueError(_(
                        "Expected one %(option_type)s '%(option)s' under Combo Choice '%(choice)s'; found %(count)s. "
                        "Use an External ID or Database ID for ambiguous names.",
                        option_type=model._fields[field_name].string, option=name,
                        choice=combo.display_name, count=len(matches),
                    ).replace("%", "%%"))
                identifiers.append(str(matches[0][0]))
            scoped[field_name] = [{".id": ",".join(identifiers)}]
        return scoped
