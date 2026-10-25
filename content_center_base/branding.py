"""Only declared brand labels change; unrelated translations remain untouched."""
LABELS = {
    "content_center_base": {
        "content_center_base.menu_catalog_root": (
            "name",
            "Content Center",
            "Central de " "Conteúdo",
        ),
        "content_center_base.module_category_content_catalog": (
            "name",
            "Content " "Center",
            "Central " "de " "Conteúdo",
        ),
        "base.module_content_center_base": (
            "shortdesc",
            "Content Center",
            "Central de Conteúdo",
        ),
    },
    "content_center_sale": {
        "base.module_content_center_sale": (
            "shortdesc",
            "Content Center - Sales",
            "Central de Conteúdo - " "Vendas",
        )
    },
}


def apply_branding(env, module):
    codes = {code for code, _label in env["res.lang"].get_installed()} | {"en_US"}
    for xmlid, (field, english, portuguese) in LABELS[module].items():
        record = env.ref(xmlid)
        for code in sorted(codes - {"en_US"}) + ["en_US"]:
            record.with_context(lang=code).write(
                {field: portuguese if code == "pt_BR" else english}
            )
