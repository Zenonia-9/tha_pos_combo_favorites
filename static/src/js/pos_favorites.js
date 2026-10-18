/** @odoo-module */

import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { ProductsWidget } from "@point_of_sale/app/screens/product_screen/product_list/product_list";

const FAVORITES_CATEGORY_ID = -1;

patch(ProductsWidget.prototype, {
    getCategories() {
        const favoriteCategory = {
            id: FAVORITES_CATEGORY_ID,
            name: _t("Favorites"),
            icon: "fa-star fa-2x text-warning",
        };
        if (this.pos.selectedCategoryId === FAVORITES_CATEGORY_ID) {
            return [
                {
                    id: this.pos.db.root_category_id,
                    name: "",
                    icon: "fa-home fa-2x",
                },
                favoriteCategory,
            ];
        }
        const categories = super.getCategories(...arguments);
        const rootCategoryIndex = categories.findIndex(
            (category) => category.id === this.pos.db.root_category_id
        );
        categories.splice(rootCategoryIndex + 1, 0, favoriteCategory);
        return categories;
    },

    get productsToDisplay() {
        if (this.pos.selectedCategoryId !== FAVORITES_CATEGORY_ID) {
            return super.productsToDisplay;
        }
        const { db } = this.pos;
        const products = this.searchWord
            ? db.search_product_in_category(db.root_category_id, this.searchWord)
            : db.get_product_by_category(db.root_category_id);
        return products
            .filter(
                (product) =>
                    product.tha_is_favorite &&
                    !this.getProductListToNotDisplay().includes(product.id)
            )
            .sort((a, b) => a.display_name.localeCompare(b.display_name));
    },
});
