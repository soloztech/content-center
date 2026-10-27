from odoo import SUPERUSER_ID, api

from odoo.addons.content_center_base.branding import apply_branding
from odoo.addons.content_center_base.transition import (
    clear_upgrade_checkpoint,
    guard_parallel_install,
    retire_legacy_aliases,
)


def pre_init_hook(cr):
    env = api.Environment(cr, SUPERUSER_ID, {"lang": None})
    guard_parallel_install(env, "content_center_contact_center")


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {"lang": None})
    apply_branding(env, "content_center_contact_center")


def uninstall_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {"lang": None})
    rows = (
        env["ir.model.data"]
        .sudo()
        .search([("module", "=", "marketing_center_catalog_contact_center")])
    )
    retire_legacy_aliases(env, "content_center_contact_center", rows.mapped("name"))
    clear_upgrade_checkpoint(env, "content_center_contact_center")
