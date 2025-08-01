# Copyright 2025 Logyca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import UserError


class IrModel(models.Model):
    _inherit = "ir.model"

    def _patch_quick_create(self):
        """
        Logyca Customization: Override to only block frontend quick creation
        while allowing backend operations (Helpdesk, Mail, etc.)
        """
        def _wrap_name_create():
            @api.model
            def wrapper(self, name):
                # Solo bloquear si es una llamada del frontend (tiene 'params' en contexto)
                if 'params' in self.env.context:
                    raise UserError(
                        _(
                            "Can't create %(model)s with name %(name)s quickly.\n"
                            "Please contact your system administrator to disable "
                            "this behaviour."
                        )
                        % {"model": self._name, "name": name}
                    )
                
                # Si es una llamada del backend (sin 'params'), permitir la creación
                return wrapper.origin(self, name)

            return wrapper

        method_name = "name_create"
        for model in self:
            model_obj = self.env.get(model.model)
            if model.avoid_quick_create and model_obj is not None:
                self._patch_method(model_obj, method_name, _wrap_name_create())
            else:
                method = getattr(model_obj, method_name, None)
                if method and hasattr(method, "origin"):
                    self._revert_method(model_obj, method_name)
        return True
