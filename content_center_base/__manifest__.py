{
    "name": "Content Center",
    "summary": "Company and product content, files and FAQs for sales and support",
    "version": "16.0.2.0.1",
    "category": "Marketing",
    "author": "Soloz Technologies",
    "website": "https://github.com/soloztech/content-center",
    "license": "AGPL-3",
    "depends": ["product", "mail", "web", "web_editor"],
    "data": [
        "security/catalog_security.xml",
        "security/ir.model.access.csv",
        "views/catalog_item_views.xml",
        "views/catalog_subject_views.xml",
        "views/product_views.xml",
        "views/menus.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "content_center_base/static/src/js/*.js",
            "content_center_base/static/src/xml/*.xml",
            "content_center_base/static/src/scss/*.scss",
        ],
        "web.qunit_suite_tests": [
            "content_center_base/static/tests/*.js",
        ],
    },
    "pre_init_hook": "pre_init_hook",
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
    "installable": True,
    "application": True,
    "auto_install": False,
}
