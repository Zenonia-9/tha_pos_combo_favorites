{
    "name": "POS Nested Combo Sets",
    "version": "17.0.1.0.4",
    "category": "Point of Sale",
    "summary": "Configure nested POS combo choices with selection limits",
    "description": "Create nested combo choice groups and control how many choices customers may select in each group.",
    "author": "Thein Htoo Aung",
    "license": "LGPL-3",
    "depends": ["point_of_sale"],
    "data": ["views/pos_combo_views.xml"],
    "assets": {
        "point_of_sale._assets_pos": [
            "tha_pos_combo_set/static/src/js/combo_configurator.js",
            "tha_pos_combo_set/static/src/xml/combo_configurator.xml",
        ],
    },
    "installable": True,
    "application": False,
}
