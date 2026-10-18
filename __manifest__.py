{
    "name": "POS Combo Sets and Favorites",
    "version": "17.0.1.0.12",
    "category": "Point of Sale",
    "summary": "Nested POS combo choices and a Favorite products view",
    "description": "Configure nested POS combo choices and filter POS products by the Favorite flag from the product catalog.",
    "author": "Thein Htoo Aung",
    "license": "LGPL-3",
    "depends": ["point_of_sale"],
    "data": ["views/pos_combo_views.xml"],
    "assets": {
        "point_of_sale._assets_pos": [
            "tha_pos_combo_favorites/static/src/js/combo_configurator.js",
            "tha_pos_combo_favorites/static/src/js/pos_favorites.js",
            "tha_pos_combo_favorites/static/src/xml/combo_configurator.xml",
        ],
    },
    "installable": True,
    "application": False,
}
