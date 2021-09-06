from odoo import models, api, _
from odoo.exceptions import UserError


class SendNotificationBeneficiary(models.TransientModel):
    _name = "send.notification.beneficiary"
    _description = "Wizard to send notification for beneficiaries"

    def sendNotification(self):
        context = dict(self._context or {})
        benefits = self.env['benefits.admon'].browse(context.get('active_ids'))
        draft_to_notified = benefits.filtered(lambda m: m.state == 'draft').sorted(lambda m: (m.id))
        if not draft_to_notified:
            raise UserError(_('No hay postulaciones en borrador para notificar'))
        draft_to_notified.send_notification_benefit()
        return {'type': 'ir.actions.act_window_close'}
