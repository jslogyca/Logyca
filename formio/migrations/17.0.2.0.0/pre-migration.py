# Copyright Nova Code (https://www.novacode.nl)
# See LICENSE file for full licensing details.

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    try:
        field = env.ref('formio.field_formio_builder__public_uuid')
        cr.execute('ALTER TABLE formio_builder ADD COLUMN current_uuid character varying')
        cr.execute('UPDATE formio_builder SET current_uuid = public_uuid')
    except:
        pass
