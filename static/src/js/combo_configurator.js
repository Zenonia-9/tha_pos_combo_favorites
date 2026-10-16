/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { ComboConfiguratorPopup } from "@point_of_sale/app/store/combo_configurator_popup/combo_configurator_popup";
import { useState } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";

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
        this.state = useState({
            combo: {},
            childCombos: {},
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
        const count = (this.state.combo[combo.id] || []).length
            + (this.state.childCombos[combo.id] || []).length;
        return count < (combo.tha_max_selection || 1);
    },
    toggleSelection(combo, value, isChild) {
        const key = isChild ? "childCombos" : "combo";
        const selected = [...(this.state[key][combo.id] || [])];
        const index = selected.indexOf(value);
        if (index >= 0) {
            selected.splice(index, 1);
            if (isChild) {
                this.clearSubtree(value);
            } else {
                delete this.state.configuration[value];
            }
        } else if (this.canSelect(combo, value, isChild)) {
            selected.push(value);
        }
        this.state[key][combo.id] = selected;
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
    },
    async onClickNestedProduct({ product, combo, combo_line }) {
        if (product.isConfigurable()) {
            const { confirmed, payload } = await product.openConfigurator({ initQuantity: 1 });
            if (!confirmed) {
                return;
            }
            this.state.configuration[combo_line.id] = payload;
        }
        this.toggleSelection(combo, combo_line.id, false);
    },
    areAllCombosSelected() {
        const isComplete = (combo) => {
            const children = this.getChildren(combo);
            const selectedChildren = this.state.childCombos[combo.id] || [];
            const selectedProducts = this.state.combo[combo.id] || [];
            const selectionCount = selectedChildren.length + selectedProducts.length;
            if (!selectionCount || selectionCount > (combo.tha_max_selection || 1)) {
                return false;
            }
            return selectedChildren.every((id) => isComplete(this.pos.db.combo_by_id[id]));
        };
        return this.props.product.combo_ids.every((id) => isComplete(this.pos.db.combo_by_id[id]));
    },
    getPayload() {
        const selectedLines = [];
        const visit = (combo) => {
            for (const childId of this.state.childCombos[combo.id] || []) {
                visit(this.pos.db.combo_by_id[childId]);
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
