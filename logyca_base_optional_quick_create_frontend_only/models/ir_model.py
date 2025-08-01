# Copyright 2025 Logyca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class IrModel(models.Model):
    _inherit = "ir.model"

    def _patch_quick_create(self):
        """
        Logyca Customization: Override to only block frontend quick creation
        while allowing backend operations (Helpdesk, Mail, etc.)
        """
        _logger.info("LOGYCA: Applying custom _patch_quick_create to avoid backend blocks.")

        def _wrap_name_create():
            @api.model
            def wrapper(self, name):
                # LOGYCA CUSTOM: Block only if it's a frontend call.
                # Frontend RPC calls typically include 'params' in the context.
                if 'params' in self.env.context:
                    _logger.warning(
                        "LOGYCA: Blocking frontend quick create for model %s with name %s",
                        self._name, name
                    )
                    raise UserError(
                        _(
                            "Can't create %(model)s with name %(name)s quickly.\n"
                            "Please contact your system administrator to disable "
                            "this behaviour."
                        )
                        % {"model": self._name, "name": name}
                    )

                # Allow backend calls (like email processing) to proceed.
                _logger.info(
                    "LOGYCA: Allowing backend quick create for model %s with name %s",
                    self._name, name
                )
                return wrapper.origin(self, name)

            return wrapper

        method_name = "name_create"
        for model in self:
            model_obj = self.env.get(model.model)
            if model_obj is None:
                continue

            # First, revert any existing patch from the original module to avoid double-patching
            method = getattr(type(model_obj), method_name)
            if hasattr(method, "origin"):
                self._revert_method(model_obj, method_name)

            # Now, apply the correct patch (either ours or the original logic)
            if model.avoid_quick_create:
                self._patch_method(model_obj, method_name, _wrap_name_create())

        return True
