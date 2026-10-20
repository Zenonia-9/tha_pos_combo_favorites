{
    "name": "POS Combo Sets and Favorites",
    "version": "17.0.1.0.14",
    "category": "Point of Sale",
    "summary": "Nested POS combos, availability for each set, and Favorites",
    "description": "Configure nested POS combo choices, customize available options for each combo set, and filter POS products by the Favorite flag.",
    "author": "Thein Htoo Aung",
    "license": "LGPL-3",
    "depends": ["point_of_sale"],
    "data": [
        "security/ir.model.access.csv",
        "views/pos_combo_views.xml",
        "views/combo_availability_views.xml",
    ],
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
