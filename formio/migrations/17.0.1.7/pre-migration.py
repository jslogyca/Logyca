# Copyright Nova Code (https://www.novacode.nl)
# See LICENSE file for full licensing details.

def migrate(cr, version):
    cr.execute('ALTER TABLE formio_builder ADD COLUMN backend_submission_url_add_query_params_from character varying')
    cr.execute('ALTER TABLE formio_builder ADD COLUMN portal_submission_url_add_query_params_from character varying')
    cr.execute('ALTER TABLE formio_builder ADD COLUMN public_submission_url_add_query_params_from character varying')
    cr.execute('UPDATE formio_builder SET backend_submission_url_add_query_params_from = submission_url_add_query_params_from')
    cr.execute('UPDATE formio_builder SET portal_submission_url_add_query_params_from = submission_url_add_query_params_from')
    cr.execute('UPDATE formio_builder SET public_submission_url_add_query_params_from = submission_url_add_query_params_from')
