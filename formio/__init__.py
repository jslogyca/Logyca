# Copyright Nova Code (http://www.novacode.nl)
# See LICENSE file for full licensing details.

import logging

from . import models
from . import controllers
from . import utils
from . import wizard

import odoo
from odoo import api, SUPERUSER_ID
from functools import partial

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    VersionGitHubTag = env['formio.version.github.tag']
    try:
        VersionGitHubTag.check_and_register_available_versions()
    except Exception as e:
        msg_lines = [
            'Could not immediately check and register new formio.js GitHub releases (tags).',
            'Error: %s' % e,
            'Suggestion: Check the network connection.'
        ]
        _logger.warning('\n'.join(msg_lines))
    try:
        Param = env['ir.config_parameter'].sudo()
        version_prefix = Param.get_param('formio.versions_to_register').split(',')[0]
        version_prefix_dot = '{v}.'.format(v=version_prefix)
        version_like = '{v}%'.format(v=version_prefix)
        if version_prefix:
            domain = [('name', '=ilike', version_like)]
            version_github_tags = VersionGitHubTag.search(domain).filtered(
                lambda v: '-rc.' not in v.name and '-m.' not in v.name
            )
            if version_github_tags:
                version_github_tag = version_github_tags.sorted(
                    key=lambda v: v.name.replace(version_prefix_dot, '')
                )[-1]
                version_github_tag.action_download_install()
    except Exception as e:
        version_name = version_github_tag.name
        msg_lines = [
            'Could not immediately download and install formio.js version %s.' % version_name,
            'Error: %s' % e,
            'Suggestion: Check the network connection.'
        ]
        _logger.warning('\n'.join(msg_lines))


def uninstall_hook(cr, registry):
    def delete_config_parameter(dbname):
        db_registry = odoo.modules.registry.Registry.new(dbname)
        with api.Environment.manage(), db_registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            env['ir.config_parameter'].search(
                [('key', '=', 'formio.default_builder_js_options_id')]).unlink()
    cr.postcommit.add(partial(delete_config_parameter, cr.dbname))
