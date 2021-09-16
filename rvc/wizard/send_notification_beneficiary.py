from odoo import models, api, _
from odoo.exceptions import UserError


class SendNotificationBeneficiary(models.TransientModel):
    _name = "send.notification.beneficiary"
    _description = "Wizard to send notification for beneficiaries"

    def sendNotification(self):
        context = dict(self._context or {})
        benefits = self.env['benefit.application'].browse(context.get('active_ids'))
        draft_to_notified = benefits.filtered(lambda m: m.state == 'draft' or m.state == 'notified').sorted(lambda m: (m.id))
        if not draft_to_notified:
            raise UserError(_('Entre las postulaciones seleccionadas, ninguna está en borrador o notificada para realizar este proceso'))
        draft_to_notified.send_notification_benefit()
        return {'type': 'ir.actions.act_window_close'}
