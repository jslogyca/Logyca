# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime, timedelta

class HrLeave(models.Model):
    _inherit = 'hr.leave'

    reminder_sent = fields.Boolean(
        string='Recordatorio Enviado',
        default=False,
        help='Indica si ya se envió el recordatorio 8 días antes'
    )
    day_init_leave = fields.Float('Días de Inicio', default=0.0)

    @api.model
    def _send_leave_reminders(self):
        """
        Método ejecutado por el cron para enviar recordatorios 8 días antes
        de que inicie la ausencia
        """
        today = fields.Date.context_today(self)
        reminder_date = today + timedelta(days=8)
        diferencia = today - self.request_date_from

        # Obtener los días
        dias = diferencia.days
        self.day_init_leave = dias
        
        # Buscar ausencias aprobadas que:
        # - Inician en 8 días
        # - No se les ha enviado recordatorio
        # - Son de tipo vacaciones o similares
        leaves = self.search([
            ('state', '=', 'validate'),
            ('request_date_from', '>=', today),
            ('request_date_from', '<=', reminder_date),
            ('employee_id.work_email', '!=', False),
        ])

        template = self.env.ref('website_leave_form.email_template_leave_reminder', raise_if_not_found=False)
        
        if not template:
            return
        
        sent_count = 0
        for leave in leaves:
            try:
                # Enviar email al empleado
                template.send_mail(
                    leave.id,
                    force_send=True,
                    email_values={
                        'email_to': leave.employee_id.work_email,
                    }
                )
                
                # Marcar como enviado
                leave.write({'reminder_sent': True})
                sent_count += 1
                
            except Exception as e:
                # Log error pero continuar con los demás
                self.env['ir.logging'].sudo().create({
                    'name': 'Leave Reminder Error',
                    'type': 'server',
                    'level': 'error',
                    'message': f'Error enviando recordatorio a {leave.employee_id.name}: {str(e)}',
                    'path': 'hr.leave',
                    'func': '_send_leave_reminders',
                    'line': '0',
                })
        
        return sent_count
