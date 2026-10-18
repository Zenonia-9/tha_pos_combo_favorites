/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { ComboConfiguratorPopup } from "@point_of_sale/app/store/combo_configurator_popup/combo_configurator_popup";
import { useState } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";

patch(PosStore.prototype, {
    async _processData(loadedData) {
        await super._processData(...arguments);
        const lineIds = new Set();
        for (const combo of loadedData["pos.combo"]) {
            for (const lineId of combo.combo_line_ids || []) {
                lineIds.add(lineId);
            }
        }
        const productIds = [...new Set([...lineIds]
            .map((id) => this.db.combo_line_by_id[id]?.product_id?.[0])
            .filter((id) => id && !this.db.get_product_by_id(id)))];
        if (productIds.length) {
            const products = await this._loadProductByIds(productIds);
            await this._loadMissingPricelistItems(products);
            this._loadProductProduct(products);
        }
    },
});

patch(ComboConfiguratorPopup.prototype, {
    setup() {
        super.setup(...arguments);
        this.pos = usePos();
        this.popup = useService("popup");
        this.state = useState({
            combo: {},
            childCombos: {},
            nestedPayload: {},
            configuration: {},
        });
    },
    getChildren(combo) {
        return (combo.tha_child_combo_ids || [])
            .map((id) => this.pos.db.combo_by_id[id])
            .filter(Boolean);
    },
    getAvailableComboLines(combo) {
        return (combo.combo_line_ids || [])
            .map((id) => this.pos.db.combo_line_by_id[id])
            .filter((line) => line && this.pos.db.product_by_id[line.product_id[0]]?.active);
    },
    isSelected(comboId, value, isChild = false) {
        const selected = isChild ? this.state.childCombos : this.state.combo;
        return (selected[comboId] || []).includes(value);
    },
    canSelect(combo, value, isChild = false) {
        if (this.isSelected(combo.id, value, isChild)) {
            return true;
        }
        const maxSelection = combo.tha_max_selection || 1;
        const count = (this.state.combo[combo.id] || []).length
            + (this.state.childCombos[combo.id] || []).length;
        // A single-select choice behaves like native radio buttons: selecting a
        // different option replaces the previous selection.
        return maxSelection === 1 || count < maxSelection;
    },
    toggleSelection(combo, value, isChild) {
        const key = isChild ? "childCombos" : "combo";
        const selected = [...(this.state[key][combo.id] || [])];
        const index = selected.indexOf(value);
        if (index >= 0) {
            if ((combo.tha_max_selection || 1) === 1) {
                return;
            }
            selected.splice(index, 1);
            if (isChild) {
                this.clearSubtree(value);
            } else {
                delete this.state.configuration[value];
            }
        } else if (this.canSelect(combo, value, isChild)) {
            if ((combo.tha_max_selection || 1) === 1) {
                for (const childId of this.state.childCombos[combo.id] || []) {
                    this.clearSubtree(childId);
                    delete this.state.nestedPayload[combo.id]?.[childId];
                }
                for (const lineId of this.state.combo[combo.id] || []) {
                    delete this.state.configuration[lineId];
                }
                this.state.childCombos[combo.id] = [];
                this.state.combo[combo.id] = [];
                // `selected` is a local copy of the prior selection. Clear it too
                // before storing the replacement below.
                selected.length = 0;
            }
            selected.push(value);
        }
        this.state[key][combo.id] = selected;
    },
    async onClickNestedCombo(combo, child) {
        const wasSelected = this.isSelected(combo.id, child.id, true);
        const { confirmed, payload } = await this.popup.add(ComboConfiguratorPopup, {
            product: { display_name: child.name, combo_ids: [child.id] },
        });
        if (!confirmed) {
            return;
        }
        if (!wasSelected) {
            this.toggleSelection(combo, child.id, true);
        }
        this.state.nestedPayload[combo.id] ||= {};
        this.state.nestedPayload[combo.id][child.id] = payload;
    },
    getNestedSelectionSummary(combo, child) {
        return (this.state.nestedPayload[combo.id]?.[child.id] || [])
            .map((line) => this.pos.db.product_by_id[line.product_id[0]]?.display_name
                || line.product_id[1])
            .join(", ");
    },
    getNestedSelectionLabel(combo, child) {
        const count = (this.state.nestedPayload[combo.id]?.[child.id] || []).length;
        return count === 1 ? "Selected product" : "Selected products";
    },
    removeNestedCombo(combo, child) {
        this.toggleSelection(combo, child.id, true);
        delete this.state.nestedPayload[combo.id]?.[child.id];
    },
    clearSubtree(comboId) {
        const combo = this.pos.db.combo_by_id[comboId];
        for (const child of this.getChildren(combo || {})) {
            this.clearSubtree(child.id);
        }
        for (const line of this.getAvailableComboLines(combo || {})) {
            delete this.state.configuration[line.id];
        }
        delete this.state.combo[comboId];
        delete this.state.childCombos[comboId];
        delete this.state.nestedPayload[comboId];
    },
    async onClickNestedProduct({ product, combo, combo_line }) {
        const wasSelected = this.isSelected(combo.id, combo_line.id);
        if (product.isConfigurable()) {
            const { confirmed, payload } = await product.openConfigurator({ initQuantity: 1 });
            if (!confirmed) {
                return;
            }
            this.state.configuration[combo_line.id] = payload;
        }
        if (!wasSelected) {
            this.toggleSelection(combo, combo_line.id, false);
        }
    },
    areAllCombosSelected() {
        const isComplete = (combo) => {
            const selectedChildren = this.state.childCombos[combo.id] || [];
            const selectedProducts = this.state.combo[combo.id] || [];
            const selectionCount = selectedChildren.length + selectedProducts.length;
            if (!selectionCount || selectionCount > (combo.tha_max_selection || 1)) {
                return false;
            }
            // Each nested popup owns its selection state. Its confirmed payload,
            // rather than this popup's local arrays, records completed choices.
            return selectedChildren.every((id) =>
                (this.state.nestedPayload[combo.id]?.[id] || []).length > 0);
        };
        return this.props.product.combo_ids.every((id) => isComplete(this.pos.db.combo_by_id[id]));
    },
    getPayload() {
        const selectedLines = [];
        const visit = (combo) => {
            for (const childId of this.state.childCombos[combo.id] || []) {
                selectedLines.push(...(this.state.nestedPayload[combo.id]?.[childId] || []));
            }
            for (const id of this.state.combo[combo.id] || []) {
                const combo_line = this.pos.db.combo_line_by_id[id];
                selectedLines.push({ ...combo_line, configuration: this.state.configuration[id] });
            }
        };
        for (const id of this.props.product.combo_ids) {
            visit(this.pos.db.combo_by_id[id]);
        }
        return selectedLines;
    },
});
