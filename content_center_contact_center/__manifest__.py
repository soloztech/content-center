{
    "name": "Content Center - Contact Center",
    "summary": "Find company and product content and add it to conversation drafts",
    "version": "16.0.2.0.0",
    "category": "Sales/CRM",
    "author": "Soloz Technologies",
    "website": "https://github.com/soloztech/content-center",
    "license": "AGPL-3",
    "depends": ["content_center_base", "contact_center_ui"],
    "assets": {
        "web.assets_backend": [
            "content_center_contact_center/static/src/js/catalog_dialog.esm.js",
            "content_center_contact_center/static/src/js/message_composer.esm.js",
            "content_center_contact_center/static/src/xml/*.xml",
            "content_center_contact_center/static/src/scss/catalog_dialog.scss",
        ],
        "web.qunit_suite_tests": [
            "content_center_contact_center/static/tests/*.esm.js",
        ],
    },
    "pre_init_hook": "pre_init_hook",
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
    "installable": True,
    "application": False,
    "auto_install": False,
}
