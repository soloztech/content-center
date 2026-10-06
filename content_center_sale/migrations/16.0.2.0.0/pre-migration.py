from odoo import SUPERUSER_ID, api

from odoo.addons.content_center_base.transition import validate_prepared


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {"lang": None})
    validate_prepared(env)
