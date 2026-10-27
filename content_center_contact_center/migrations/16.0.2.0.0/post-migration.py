from odoo import SUPERUSER_ID, api

from odoo.addons.content_center_base.branding import apply_branding
from odoo.addons.content_center_base.transition import upgrade_checkpoint


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {"lang": None})
    apply_branding(env, "content_center_contact_center")
    upgrade_checkpoint(env, "content_center_contact_center")
