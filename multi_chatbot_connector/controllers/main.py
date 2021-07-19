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
from odoo.addons.im_livechat.controllers.main import LivechatController
from odoo import http, _
from odoo.http import request
import logging
import re
import os
from os import environ
import json
import requests
from binascii import Error as binascii_error
from collections import defaultdict
from operator import itemgetter
from odoo.http import request
from odoo import _, api, fields, models, modules, tools
from odoo.exceptions import UserError, AccessError
from odoo.osv import expression
from odoo.tools import groupby

class LivechatMultiController(LivechatController):
    
    @http.route('/get/current/chatbot_connector', type='json',website=True, auth='public')
    def get_current_chatbot_connector(self,uuid,**kwargs):
        if not uuid:
            return False
        channel = request.env['mail.channel'].sudo().search([('uuid', '=', uuid)], limit=1)
        if not channel:
            return False
        mail_channel = channel.livechat_channel_id if channel.livechat_channel_id else False
        if not mail_channel:
            return False
        if not mail_channel.multi_chatbot:
            return False
        return mail_channel.multi_chatbot
    
    @http.route('/get/current/options/chatbot_connector', type='json',website=True, auth='public')
    def get_current_options_chatbot_connector(self,uuid,**kwargs):
        if not uuid:
            return False
        mail_channel = request.env['im_livechat.channel'].sudo().search([('id', '=', uuid)],limit=1)
        if not mail_channel:
            return False
        if not mail_channel.multi_chatbot:
            return False
        return mail_channel.multi_chatbot
    
    @http.route('/im_livechat/support/<int:channel_id>', type='http', auth='public')
    def support_page(self, channel_id, **kwargs):
        res = super(LivechatMultiController, self).support_page(channel_id=channel_id, **kwargs)
#         channel_mi = request.env['im_livechat.channel'].sudo().browse(channel_id)
#         if channel_mi and channel_mi.multi_chatbot:
        mail_chat = kwargs.get('help_id', False)
        mail_chat_id = request.env['mail.channel'].sudo().browse(int(mail_chat))
        if mail_chat:
            res.qcontext.update({'mail_chat':int(mail_chat),'chat_status':mail_chat_id.helpdesk_lead_id.status})
        return res
    
    @http.route('/im_livechat/get_session', type="json", auth='public', website=True)
    def get_session(self, channel_id, anonymous_name, mail_chat=None, **kwargs):
        res = super(LivechatMultiController, self).get_session(channel_id=channel_id, anonymous_name=anonymous_name,mail_chat=mail_chat, **kwargs)
#         channel_mi = request.env['im_livechat.channel'].sudo().browse(channel_id)
#         if channel_mi and channel_mi.multi_chatbot:
        if mail_chat:
            Channel = request.env['mail.channel']
            channel = Channel.sudo().browse(int(mail_chat))
            if channel and channel.helpdesk_lead_id.status in ['new','working']:
                res.update({'id':channel.id,
                            'name':channel.display_name,
                            'uuid':channel.uuid,
                            'anonymous_name':channel.anonymous_name})
        if request.website.user_id != request.env.user:
            res.update({'user_id':request.env.user.id,
                        'user_name':request.env.user.name,
                        'user_login':request.env.user.login,})
        return res
    
    @http.route('/im_livechat/feedback', type='json', auth='public')
    def feedback(self, uuid, rate, reason=None, **kwargs):
        res = super(LivechatMultiController, self).feedback(uuid=uuid, rate=rate, reason=reason, **kwargs)
        Channel = request.env['mail.channel']
        channel = Channel.sudo().search([('uuid', '=', uuid)], limit=1)
        if channel and channel.helpdesk_lead_id:
            channel.helpdesk_lead_id.sudo().write({'status':'finish','rating':str(rate)})
            request.env.user.write({'is_busy':False})
            channel.helpdesk_lead_id.send_by_chat_history_mail()
        return res
    
    @http.route('/check/lead/post', type="json", auth='public')
    def CheckLeadPost(self, uuid, location=False, **kwargs):
        Channel = request.env['mail.channel']
        if uuid and Channel.sudo().search([('uuid', '=', uuid)], limit=1):
            Channel_id =  Channel.sudo().search([('uuid', '=', uuid)], limit=1)
            return Channel_id.helpdesk_lead_id.id if Channel_id.helpdesk_lead_id else False
        else:
            return False

    @http.route('/user/info', type="json", auth="public")
    def UserInformation(self, user_id=False ,**kwargs):
        if user_id:
            user_obj=request.env['res.users'].sudo().search([('id','=',user_id)])
            val={'name':user_obj.name,'email':user_obj.login}
            return val
        else:
            return False

    @http.route('/isuue/category/', type="json", auth='public')
    def IssueCategory(self, **kwargs):
        Categorylist = []
        online_help_category = request.env['online.help.category'].sudo().search([])
        livechat_channel = request.env['im_livechat.channel'].sudo().search([('issue_category','in',online_help_category.ids),('company_id','=',request.env.user.company_id.id)])
        for categ in livechat_channel:
            val = {'id':categ.issue_category.id, 'name':categ.issue_category.name}
            Categorylist.append(val)
        return Categorylist

    @http.route('/lead/submit', type="json", auth='public')
    def LeadSubmit(self, uuid, helpdesk_info, **kwargs):
        Channel = request.env['mail.channel']
        HelpDesk = request.env['online.helpdesk']
        Maillist = request.env['mailing.contact']
        Im_Livechat = request.env['im_livechat.channel']
        Channel_id =  Channel.sudo().search([('uuid', '=', uuid)], limit=1)
        issue_category = helpdesk_info.get('issue_category', False)
        livechat = Im_Livechat.sudo().search([('issue_category','=',int(issue_category)),('company_id','=',request.env.user.company_id.id)])
        if uuid and Channel_id and livechat:
            Channel_id.write({'livechat_channel_id':livechat.id})
            available = Channel_id.livechat_channel_id._get_available_users()
            if issue_category:
                available_users = request.env['res.users'].sudo().search([('id','in',available.ids),
                                                                          ('issue_category','=',int(issue_category)),
                                                                          ('is_busy','=',False)], limit=1).partner_id
                if not available_users:
                    available_users = request.env['res.users'].sudo().search([('id','in',available.ids),
                                                                          ('issue_category','=',int(issue_category)),
                                                                          ('is_busy','=',True)], limit=1).partner_id
                Channel_id.write({'channel_partner_ids':[(6, 0, available_users.ids)]})
            helpdesk_info.update({'maill_channel_id':Channel_id.id,
                                  'company_id':livechat.company_id.id
                                  })
            helpdesk_id = HelpDesk.sudo().create(helpdesk_info)
            Channel_id.helpdesk_lead_id = helpdesk_id.id
            Maillist.sudo().create({
                            # 'list_id' :helpdesk_id.maill_channel_id.livechat_channel_id.mailing_list_id.id if helpdesk_id.maill_channel_id.livechat_channel_id.mailing_list_id else False,
                             'email':helpdesk_id.email,
                             'name':helpdesk_id.name})
            Channel_id.name  = str(helpdesk_info.get('name')) + ', ' + str((Channel_id.name))
            return {'timer':Channel_id.livechat_channel_id.timer,'msg':{'content':Channel_id.livechat_channel_id.default_message}} if Channel_id.livechat_channel_id.timer and Channel_id.livechat_channel_id.multi_chatbot else True
        else:
            return False
