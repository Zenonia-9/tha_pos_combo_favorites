from types import SimpleNamespace
from unittest.mock import patch

from odoo import Command
from odoo.tests import TransactionCase, tagged
from odoo.addons.web.controllers.export import ExcelExport


@tagged("post_install", "-at_install")
class TestComboImport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.products = cls.env["product.template"].with_context(import_file=True)
        cls.foods = cls.env["product.product"].create([
            {"name": name, "default_code": code, "available_in_pos": True}
            for name, code in [
                ("THA Combo Chicken", "THA-CB-CHICKEN"),
                ("THA Combo Pork", "THA-CB-PORK"),
                ("THA Combo Coke", "THA-CB-COKE"),
                ("THA Combo Pepsi", "THA-CB-PEPSI"),
                ("THA Combo Soju", "THA-CB-SOJU"),
            ]
        ])
        cls.chicken, cls.pork, cls.coke, cls.pepsi, cls.soju = cls.foods
        cls.combo = cls.env["pos.combo"]
        cls.meal = cls.combo.create({
            "name": "THA Import Meal",
            "combo_line_ids": [Command.create({"product_id": product.id}) for product in cls.foods[:2]],
        })
        cls.soft = cls.combo.create({
            "name": "THA Import Soft Drinks",
            "combo_line_ids": [Command.create({"product_id": product.id}) for product in cls.foods[2:4]],
        })
        cls.juice = cls.combo.create({
            "name": "THA Import Juices",
            "combo_line_ids": [Command.create({"product_id": cls.pepsi.id})],
        })
        cls.drinks = cls.combo.create({
            "name": "THA Import Drinks",
            "combo_line_ids": [Command.create({"product_id": cls.soju.id})],
            "tha_child_combo_ids": [Command.set((cls.soft | cls.juice).ids)],
        })
        cls.columns = [
            "id", "name", "detailed_type", "tha_combo_availability_ids/combo_id",
            "tha_combo_availability_ids/product_ids", "tha_combo_availability_ids/child_combo_ids",
        ]
        for name, record in [("meal", cls.meal), ("drinks", cls.drinks), ("soft", cls.soft),
                             ("chicken", cls.chicken), ("pork", cls.pork), ("coke", cls.coke)]:
            cls.env["ir.model.data"].create({
                "module": "__import__", "name": "tha_combo_" + name,
                "model": record._name, "res_id": record.id,
            })

    def import_product(self, rows, columns=None):
        rows = [["" if value is False or value is None else str(value) for value in row] for row in rows]
        result = self.products.load(columns or self.columns, rows)
        self.assertTrue(result["ids"], result)
        self.assertFalse([message for message in result["messages"] if message["type"] == "error"], result)
        return self.products.browse(result["ids"])

    def rule(self, product, combo):
        return product.tha_combo_availability_ids.filtered(lambda record: record.combo_id == combo)

    def make_set(self):
        return self.env["product.template"].create({
            "name": "THA Export Combo Set", "detailed_type": "combo",
            "combo_ids": [Command.set((self.meal | self.drinks).ids)],
        })

    def assert_import_error(self, rows, columns=None, text=None):
        result = self.products.load(columns or self.columns, rows)
        self.assertFalse(result["ids"], result)
        errors = [message["message"] for message in result["messages"] if message["type"] == "error"]
        self.assertTrue(errors, result)
        if text:
            self.assertTrue(any(text in message for message in errors), result)

    def test_names_are_scoped_to_the_selected_choice(self):
        self.env["product.product"].create({"name": self.chicken.name, "available_in_pos": True})
        self.combo.create({"name": self.soft.name})
        product = self.import_product([
            ["__import__.tha_combo_scoped", "THA Scoped Set", "combo", self.meal.name, self.chicken.name, ""],
            ["", "", "", self.drinks.name, "", self.soft.name],
        ])
        self.assertEqual(self.rule(product, self.meal).product_ids, self.chicken)
        self.assertEqual(self.rule(product, self.drinks).child_combo_ids, self.soft)

    def test_vertical_and_comma_options_with_reversed_columns(self):
        columns = [self.columns[index] for index in [0, 1, 2, 4, 5, 3]]
        first, second = self.import_product([
            ["__import__.tha_combo_vertical_a", "THA Vertical A", "combo", self.chicken.name, "", self.meal.name],
            ["", "", "", " " + self.pork.name, "", ""],
            ["", "", "", "", self.soft.name, self.drinks.name],
            ["", "", "", "", self.juice.name, ""],
            ["__import__.tha_combo_vertical_b", "THA Vertical B", "combo", self.pork.name, "", self.meal.name],
        ], columns)
        self.assertEqual(self.rule(first, self.meal).product_ids, self.foods[:2])
        self.assertEqual(self.rule(first, self.drinks).child_combo_ids, self.soft | self.juice)
        self.assertEqual(self.rule(second, self.meal).product_ids, self.pork)
        self.assertEqual(second.combo_ids, self.meal)

    def test_continuation_does_not_cross_product_boundaries(self):
        self.assert_import_error([
            ["__import__.tha_combo_boundary_a", "THA Boundary A", "combo", self.meal.name, self.chicken.name, ""],
            ["__import__.tha_combo_boundary_b", "THA Boundary B", "combo", "", self.pork.name, ""],
        ], text="Combo Choice is required")

    def test_missing_and_ambiguous_options_are_rejected(self):
        self.assert_import_error([
            ["__import__.tha_combo_wrong_product", "THA Invalid Set", "combo", self.meal.name, self.coke.name, ""],
        ], text=self.coke.name)
        self.assert_import_error([
            ["__import__.tha_combo_wrong_child", "THA Invalid Child", "combo", self.drinks.name, "", self.meal.name],
        ], text=self.meal.name)
        duplicate = self.env["product.product"].create({"name": self.chicken.name, "available_in_pos": True})
        self.meal.write({"combo_line_ids": [Command.create({"product_id": duplicate.id})]})
        self.assert_import_error([
            ["__import__.tha_combo_ambiguous_option", "THA Ambiguous Option", "combo", self.meal.name, self.chicken.name, ""],
        ], text="found 2")

    def test_ambiguous_combo_is_rejected(self):
        self.combo.create({"name": self.meal.name})
        self.assert_import_error([
            ["__import__.tha_combo_ambiguous", "THA Ambiguous Set", "combo", self.meal.name, self.chicken.name, ""],
        ], text="ambiguous")

    def test_external_and_database_references_support_continuations(self):
        for reference in ["id", ".id"]:
            columns = self.columns[:3] + [
                "tha_combo_availability_ids/combo_id/" + reference,
                "tha_combo_availability_ids/product_ids/" + reference,
            ]
            meal = "__import__.tha_combo_meal" if reference == "id" else str(self.meal.id)
            chicken = "__import__.tha_combo_chicken" if reference == "id" else str(self.chicken.id)
            pork = "__import__.tha_combo_pork" if reference == "id" else str(self.pork.id)
            product = self.import_product([
                ["__import__.tha_combo_refs_" + ("external" if reference == "id" else "database"), "THA Reference Set " + reference, "combo", meal, chicken],
                ["", "", "", "", pork],
            ], columns)
            self.assertEqual(self.rule(product, self.meal).product_ids, self.foods[:2])

    def test_nested_rows_are_inferred_in_any_order(self):
        product = self.import_product([
            ["__import__.tha_combo_nested", "THA Nested Set", "combo", self.soft.name, self.coke.name, ""],
            ["", "", "", self.drinks.name, "", self.soft.name],
        ])
        self.assertEqual(product.combo_ids, self.drinks)
        self.assertFalse(self.rule(product, self.soft).is_root)
        self.assertEqual(self.rule(product, self.soft).product_ids, self.coke)
        self.assertEqual(product.tha_combo_availability[str(self.soft.id)]["product_ids"], self.coke.ids)

    def test_sub_choice_ids_and_blank_reset(self):
        product = self.make_set()
        product_xmlid = product.export_data(["id"])["datas"][0][0]
        for reference, choice, child in [
            ("id", "__import__.tha_combo_drinks", "__import__.tha_combo_soft"),
            (".id", str(self.drinks.id), str(self.soft.id)),
        ]:
            columns = ["id", "tha_combo_availability_ids/combo_id/" + reference,
                       "tha_combo_availability_ids/child_combo_ids/" + reference]
            self.import_product([[product_xmlid, choice, child]], columns)
            self.assertEqual(self.rule(product, self.drinks).child_combo_ids, self.soft)
            self.import_product([[product_xmlid, choice, ""]], columns)
            self.assertEqual(self.rule(product, self.drinks).child_combo_ids, self.soft | self.juice)

    def test_explicit_ids_cannot_bypass_membership(self):
        for option, invalid, message in [
            ("product_ids", self.coke, "Products must belong"),
            ("child_combo_ids", self.soft, "Sub Choices must belong"),
        ]:
            self.assert_import_error([
                ["__import__.tha_combo_invalid_ids", "THA Invalid IDs", "combo",
                 str(self.meal.id), str(invalid.id)],
            ], self.columns[:3] + ["tha_combo_availability_ids/combo_id/.id",
                                  "tha_combo_availability_ids/" + option + "/.id"], text=message)

    def test_updates_preserve_omitted_choices_and_blank_resets(self):
        product = self.make_set()
        product_xmlid = product.export_data(["id"])["datas"][0][0]
        original_ids = product.tha_combo_availability_ids.ids
        self.import_product([
            [product_xmlid, product.name, "combo", self.meal.name, self.pork.name, ""],
        ])
        self.assertEqual(product.combo_ids, self.meal | self.drinks)
        self.assertEqual(product.tha_combo_availability_ids.ids, original_ids)
        self.assertEqual(self.rule(product, self.meal).product_ids, self.pork)
        self.import_product([[product_xmlid, product.name, "combo", self.meal.name, "", ""]])
        self.assertEqual(self.rule(product, self.meal).product_ids, self.foods[:2])
        self.assertEqual(product.tha_combo_availability_ids.ids, original_ids)

    def test_option_columns_not_imported_are_unchanged(self):
        product = self.make_set()
        self.rule(product, self.meal).write({"product_ids": [Command.set(self.pork.ids)]})
        product_xmlid = product.export_data(["id"])["datas"][0][0]
        self.import_product([[product_xmlid, self.meal.name]], [self.columns[0], self.columns[3]])
        self.assertEqual(self.rule(product, self.meal).product_ids, self.pork)

    def test_native_export_roundtrip_with_names_and_ids(self):
        product = self.make_set()
        self.rule(product, self.soft).write({"product_ids": [Command.set(self.coke.ids)]})
        original = product.tha_combo_availability
        original_ids = product.tha_combo_availability_ids.ids
        layouts = [
            ["id", "name", "tha_combo_availability_ids/combo_id", "tha_combo_availability_ids/product_ids", "tha_combo_availability_ids/child_combo_ids"],
            ["id", "name", "tha_combo_availability_ids/id", "tha_combo_availability_ids/combo_id/id", "tha_combo_availability_ids/product_ids/id", "tha_combo_availability_ids/child_combo_ids/id"],
            # Native Odoo exports M2M /.id as display names; use its supported name columns.
            [".id", "name", "tha_combo_availability_ids/.id", "tha_combo_availability_ids/combo_id/.id", "tha_combo_availability_ids/product_ids", "tha_combo_availability_ids/child_combo_ids"],
        ]
        for columns in layouts:
            rows = product.with_context(import_compat=True).export_data(columns)["datas"]
            imported = self.import_product(rows, columns)
            self.assertEqual(imported, product)
            self.assertEqual(product.combo_ids, self.meal | self.drinks)
            self.assertEqual(product.tha_combo_availability, original)
            self.assertEqual(product.tha_combo_availability_ids.ids, original_ids)

    def test_referenced_line_without_combo_column(self):
        product = self.make_set()
        rule = self.rule(product, self.meal)
        rule_xmlid = rule.export_data(["id"])["datas"][0][0]
        product_xmlid = product.export_data(["id"])["datas"][0][0]
        self.import_product([
            [product_xmlid, rule_xmlid, self.chicken.name],
            ["", "", self.pork.name],
        ], ["id", "tha_combo_availability_ids/id", "tha_combo_availability_ids/product_ids"])
        self.assertEqual(rule.product_ids, self.foods[:2])

    def test_line_reference_cannot_move_between_products(self):
        source = self.make_set()
        rule = self.rule(source, self.meal)
        row_xmlid = rule.export_data(["id"])["datas"][0][0]
        self.assert_import_error([
            ["__import__.tha_combo_stolen", "THA New Set", "combo", row_xmlid, self.meal.name, self.chicken.name],
        ], ["id", "name", "detailed_type", "tha_combo_availability_ids/id", "tha_combo_availability_ids/combo_id", "tha_combo_availability_ids/product_ids"], text="another product")
        self.assertEqual(rule.product_tmpl_id, source)

    def test_native_xlsx_export_import(self):
        product = self.make_set()
        columns = ["id", "name", "tha_combo_availability_ids/id", "tha_combo_availability_ids/combo_id", "tha_combo_availability_ids/product_ids", "tha_combo_availability_ids/child_combo_ids"]
        rows = product.with_context(import_compat=True).export_data(columns)["datas"]
        original_ids = product.tha_combo_availability_ids.ids
        with patch("odoo.addons.web.controllers.export.request", SimpleNamespace(env=self.env)):
            contents = ExcelExport().from_data(columns, rows)
        wizard = self.env["base_import.import"].create({
            "res_model": "product.template", "file": contents, "file_name": "products.xlsx",
            "file_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        })
        result = wizard.execute_import(columns, columns, {"has_headers": True, "skip": 0})
        self.assertTrue(result["ids"], result)
        self.assertEqual(result["ids"], product.ids)
        self.assertEqual(product.tha_combo_availability_ids.ids, original_ids)

    def test_attribute_import_converter_still_scopes_values(self):
        if not hasattr(self.env["ir.fields.converter"], "tha_scope_attribute_values"):
            self.skipTest("THA Product Attribute Import is not installed")
        attribute, other = self.env["product.attribute"].create([
            {"name": "THA Combo Compatibility Choice", "create_variant": "no_variant"},
            {"name": "THA Combo Compatibility Other", "create_variant": "no_variant"},
        ])
        values = self.env["product.attribute.value"].create([
            {"name": "Chicken", "attribute_id": attribute.id},
            {"name": "Pork", "attribute_id": attribute.id},
            {"name": "Chicken", "attribute_id": other.id},
        ])
        product = self.import_product([
            ["__import__.tha_combo_compatibility", "THA Attribute Compatibility", attribute.name, "Chicken"],
            ["", "", "", "Pork"],
        ], ["id", "name", "attribute_line_ids/attribute_id", "attribute_line_ids/value_ids"])
        self.assertEqual(product.attribute_line_ids.value_ids, values[:2])
