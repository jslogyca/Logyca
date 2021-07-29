# -*- coding: utf-8 -*-
###############################################################################
#
#   Copyright (C) 2004-today OpenERP SA (<http://www.openerp.com>)
#   Copyright (C) 2016-today Geminate Consultancy Services (<http://geminatecs.com>).
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import models, fields, api, _
from datetime import datetime,timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from calendar import monthrange
from collections import OrderedDict
import time

class ReportMonthChannelTemplate(models.AbstractModel):
    _name = 'report.multi_chatbot_connector.report_month_channel_template'
    
    def months_between(self, start, end):
        months = []
        cursor = datetime.strptime(str(start), DEFAULT_SERVER_DATE_FORMAT)
        while cursor < datetime.strptime(str(end), DEFAULT_SERVER_DATE_FORMAT):
            if cursor.month not in months:
                months.append((str(cursor.year)+'-'+str(cursor.month)+'-01', str(cursor.year)+'-'+ str(cursor.month)+'-'+str(monthrange(cursor.year, cursor.month)[1])))
            cursor += timedelta(weeks=1)
        return OrderedDict((m, True) for m in months).keys()
    
    @api.model
    def _get_report_values(self, docids, data=None):
        Report = self.env['ir.actions.report']._get_report_from_name('multi_chatbot_connector.report_month_channel_template')
        channels = self.env['im_livechat.channel'].browse(data['form'][0].get('channel_ids', []))
        fromdate = False; todate = False
        year = data['form'][0].get('year', False)
        if data['form'][0].get('by_periods') == 'y' and year:
            fromdate = str(year)+'-01-01'
            todate = str(year)+'-12-31'
            data['form'][0].update({'from_date':fromdate,'to_date':todate})
        else:
            fromdate = data['form'][0].get('from_date', False)
            todate = data['form'][0].get('to_date', False)
        monthlist = self.months_between(fromdate, todate) if fromdate and todate else []
        UserScore = []
        docargs = {
            'doc_ids': data['form'][0]['channel_ids'],
            'doc_model': Report.model,
            'docs': channels,
            'form':data['form'][0],
            'monthlist':monthlist,
        }
        return docargs

class ReportManagerChannelTemplate(models.AbstractModel):
    _name = 'report.multi_chatbot_connector.report_manager_channel_template'
    
    def months_between(self, start, end):
        months = []
        cursor = datetime.strptime(str(start), DEFAULT_SERVER_DATE_FORMAT)
        while cursor < datetime.strptime(str(end), DEFAULT_SERVER_DATE_FORMAT):
            if cursor.month not in months:
                months.append((str(cursor.year)+'-'+str(cursor.month)+'-01', str(cursor.year)+'-'+ str(cursor.month)+'-'+str(monthrange(cursor.year, cursor.month)[1])))
            cursor += timedelta(weeks=1)
        return OrderedDict((m, True) for m in months).keys()

    def _get_report_values(self, docids, data=None):
        Report = self.env['ir.actions.report']._get_report_from_name('multi_chatbot_connector.report_manager_channel_template')
        channels = self.env['im_livechat.channel'].browse(data['form'][0].get('channel_ids', []))
        fromdate = False; todate = False
        year = data['form'][0].get('year', False)
        if data['form'][0].get('by_periods') == 'y' and year:
            fromdate = str(year)+'-01-01'
            todate = str(year)+'-12-31'
            data['form'][0].update({'from_date':fromdate,'to_date':todate})
        else:
            fromdate = data['form'][0].get('from_date', False)
            todate = data['form'][0].get('to_date', False)


        monthlist = self.months_between(fromdate, todate) if fromdate and todate else []
        UserScore = []
        docargs = {
            'doc_ids': data['form'][0]['channel_ids'],
            'doc_model': Report.model,
            'docs': channels,
            'form':data['form'][0],
            'monthlist':monthlist,
        }
        return docargs

class OnlineHelpdeskWz(models.TransientModel):
    _name = 'online.helpdesk.wz'
    
    is_channel = fields.Boolean('Channel(s)')
    status = fields.Selection([('new','New'),('working','In Progress'),('finish','Finish')], default='finish')
    from_date = fields.Date('From Date', default=lambda *a: fields.Datetime.to_string(fields.Datetime.now()))
    to_date = fields.Date('To Date', default=time.strftime('%Y-%m-28'))
    by_periods = fields.Selection([('m','Months'),('y','Year')],'By Period', default='m')
    year = fields.Selection([(str(num), str(num)) for num in range( ((datetime.now().year)-10),((datetime.now().year)+1) )], string='Year(s)')
    channel_id = fields.Many2one('im_livechat.channel', 'Channel')
    channel_ids = fields.Many2many('im_livechat.channel', 'wz_im_livechat_channel_rels', 'helpdesk_id', 'channel_id', string='Channel(s)')
    user_ids = fields.Many2many('res.users', 'res_users_rels', 'helpdesk_id', 'user_id', string='User(s)')
    typee = fields.Selection([('is_self','Self'),('is_manager','Manager')], 'Evaluation', default='is_manager')
    
    @api.onchange('channel_ids')
    def on_channel_ids(self):
        user_list = []
        for channel  in self.channel_ids:
            user_list += channel.user_ids.ids
        self.user_ids = list(set(user_list))
    
    def print_report(self):
        helpdesk = self.env['online.helpdesk'].search([('status','=',self.status)])
        if self.channel_ids:
            return self.channel_ids.env.ref('multi_chatbot_connector.report_channel').with_context({'discard_logo_check': True}).report_action(self.channel_ids)
    
    def print_self_report(self):
        self.ensure_one()
        data = self.read()
        datas = {
            'ids': self.channel_ids.ids,
            'model': 'im_livechat.channel',
            'form': data,
            'docs': self.channel_ids.ids,
        }
        if self.typee == 'is_self':
            return self.channel_ids.env.ref('multi_chatbot_connector.report_month_channel').report_action(self.channel_ids,data=datas)
        else:
            return self.channel_ids.env.ref('multi_chatbot_connector.report_manager_channel').report_action(self.channel_ids,data=datas)      