/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { ProductsWidget } from "@point_of_sale/app/screens/product_screen/product_list/product_list";

const FAVORITES_CATEGORY_ID = -1;

patch(ProductsWidget.prototype, {
    getCategories() {
        const favoriteCategory = {
            id: FAVORITES_CATEGORY_ID,
            name: "",
            icon: "fa-star fa-2x",
        };
        const isFavoritesSelected =
            this.pos.selectedCategoryId === FAVORITES_CATEGORY_ID;
        const pathCategories = isFavoritesSelected ? [] : super.getCategories(...arguments);
        const categories = isFavoritesSelected
            ? [...(this._thaRegularCategories || this._thaGetAllCategories())]
            : this._thaGetAllCategories(pathCategories);
        this._thaRegularCategories = categories.map((category) => ({ ...category }));
        const rootCategoryIndex = categories.findIndex(
            (category) => category.id === this.pos.db.root_category_id
        );
        categories.splice(rootCategoryIndex + 1, 0, favoriteCategory);
        return categories;
    },

    _thaGetAllCategories(pathCategories = []) {
        const { db } = this.pos;
        const rootCategoryId = db.root_category_id;
        const pathById = new Map(pathCategories.map((category) => [category.id, category]));
        const allCategories = Object.values(db.category_by_id);
        if (!allCategories.some((category) => category.id === rootCategoryId)) {
            allCategories.unshift({ id: rootCategoryId, name: "Root" });
        }
        return allCategories.map((category) => {
            const isRootCategory = category.id === rootCategoryId;
            const pathCategory = pathById.get(category.id);
            return {
                id: category.id,
                name: isRootCategory ? "" : category.name,
                icon: isRootCategory ? "fa-home fa-2x" : "",
                separator: "fa-caret-right",
                showSeparator: pathCategory?.showSeparator || false,
                imageUrl:
                    category.has_image &&
                    `/web/image?model=pos.category&field=image_128&id=${category.id}&unique=${category.write_date}`,
            };
        });
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
