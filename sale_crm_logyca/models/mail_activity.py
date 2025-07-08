# -*- coding: utf-8 -*-


from datetime import date
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _

from odoo.exceptions import ValidationError

class MailActivity(models.Model):
    _inherit = 'mail.activity'

    @api.model_create_multi
    def create(self, vals_list):
        print('KKKKKKKK', vals_list)
        # 1) Creamos las actividades normalmente
        activities = super().create(vals_list)
        today = self.env.cr.now()
        # 2) Para cada una sobre crm.lead, actualizamos el lead
        for act in activities.filtered(lambda a: a.res_model == 'crm.lead'):
            print('KKKKKKKK9999999', vals_list)
            # date_deadline es la fecha programada de la actividad
            self.env['crm.lead'].browse(act.res_id).write({
                'date_follow': today,
            })
        return activities

    def write(self, vals):
        # Si se modifica la fecha de la actividad, también actualizamos el follow
        res = super().write(vals)
        print('KKKKKKKK22222222', vals_list)
        # Solo si cambió date_deadline
        if 'date_deadline' in vals:
            for act in self.filtered(lambda a: a.res_model == 'crm.lead'):
                self.env['crm.lead'].browse(act.res_id).write({
                    'date_follow': act.date_deadline,
                })
        return res