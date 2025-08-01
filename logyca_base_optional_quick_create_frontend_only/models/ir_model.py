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
        _logger.info("LOGYCA: Applying custom _patch_quick_create")

        def _wrap_name_create():
            @api.model
            def wrapper(self, name):
                _logger.info("LOGYCA: name_create called for %s with name %s", self._name, name)
                _logger.info("LOGYCA: Context keys: %s", list(self.env.context.keys()))

                # LOGYCA CUSTOM: Solo bloquear si es una llamada del frontend
                # Las llamadas del frontend siempre tienen 'params' en el contexto
                if 'params' in self.env.context:
                    _logger.info("LOGYCA: Blocking frontend call")
                    raise UserError(
                        _(
                            "Can't create %(model)s with name %(name)s quickly.\n"
                            "Please contact your system administrator to disable "
                            "this behaviour."
                        )
                        % {"model": self._name, "name": name}
                    )

                # Si es una llamada del backend (sin 'params'), permitir la creación
                _logger.info("LOGYCA: Allowing backend call")
                return wrapper.origin(self, name)

            return wrapper

        method_name = "name_create"
        for model in self:
            model_obj = self.env.get(model.model)
            if model.avoid_quick_create and model_obj is not None:
                _logger.info("LOGYCA: Patching %s", model.model)
                self._patch_method(model_obj, method_name, _wrap_name_create())
            else:
                method = getattr(model_obj, method_name, None)
                if method and hasattr(method, "origin"):
                    _logger.info("LOGYCA: Reverting patch for %s", model.model)
                    self._revert_method(model_obj, method_name)
        return True

    @api.model
    def _logyca_force_repatch(self):
        """
        Método para forzar la re-aplicación del patch de Logyca
        Debe ser llamado después de que se carguen todos los módulos
        """
        _logger.info("LOGYCA: Force re-patching all models")
        quick_create_models = self.search([('avoid_quick_create', '=', True)])
        for model in quick_create_models:
            model_obj = self.env.get(model.model)
            if model_obj is not None:
                # Primero revertir cualquier patch existente
                method = getattr(model_obj, 'name_create', None)
                while method and hasattr(method, 'origin'):
                    _logger.info("LOGYCA: Removing existing patch from %s", model.model)
                    self._revert_method(model_obj, 'name_create')
                    method = getattr(model_obj, 'name_create', None)

                # Luego aplicar nuestro patch
                def _wrap_name_create():
                    @api.model
                    def wrapper(self, name):
                        # LOGYCA: Solo bloquear llamadas del frontend
                        if 'params' in self.env.context:
                            raise UserError(
                                _(
                                    "Can't create %(model)s with name %(name)s quickly.\n"
                                    "Please contact your system administrator to disable "
                                    "this behaviour."
                                )
                                % {"model": self._name, "name": name}
                            )
                        return wrapper.origin(self, name)
                    return wrapper

                _logger.info("LOGYCA: Applying custom patch to %s", model.model)
                self._patch_method(model_obj, 'name_create', _wrap_name_create())

    def _register_hook(self):
        """
        Override to ensure our customization is applied last
        """
        # Llamar al método padre primero
        result = super()._register_hook()

        # Usar un delay para asegurar que se ejecute después de todo
        self.env.cr.postcommit.add(self._logyca_force_repatch)

        return result

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to ensure our patch is applied"""
        ir_models = super().create(vals_list)
        # Forzar re-patch después de crear nuevos modelos
        self.env.cr.postcommit.add(self._logyca_force_repatch)
        return ir_models

    def write(self, vals):
        """Override write to ensure our patch is applied"""
        res = super().write(vals)
        if "avoid_quick_create" in vals:
            # Forzar re-patch después de cambios en avoid_quick_create
            self.env.cr.postcommit.add(self._logyca_force_repatch)
            self.pool.registry_invalidated = True
            self.pool.signal_changes()
        return res
