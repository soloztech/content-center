from odoo import SUPERUSER_ID, api

from .branding import apply_branding
from .transition import (
    clear_upgrade_checkpoint,
    guard_parallel_install,
    retire_legacy_aliases,
)


def pre_init_hook(cr):
    env = api.Environment(cr, SUPERUSER_ID, {"lang": None})
    guard_parallel_install(env, "content_center_base")


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {"lang": None})
    apply_branding(env, "content_center_base")


def uninstall_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {"lang": None})
    rows = (
        env["ir.model.data"]
        .sudo()
        .search([("module", "=", "marketing_center_catalog")])
    )
    retire_legacy_aliases(env, "content_center_base", rows.mapped("name"))
    clear_upgrade_checkpoint(env, "content_center_base")
