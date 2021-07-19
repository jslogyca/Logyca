# -*- coding: utf-8 -*-
###############################################################################
#
#   website_live_chatbot for Odoo
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
import re

class LivechatWebsiteController(LivechatController):
    
    @http.route('/pos_message/bot_chat', type="json", auth='public', website=True)
    def bot_chat(self, mail_chat=None, **kwargs):
        ConfigOBJ = request.env['ir.config_parameter'].sudo().get_param('multi_chatbot_connector.is_chain_of_bot')
        Message = request.env['mail.message']
        message = kwargs['message'].get('content', False) if 'message' in kwargs and 'content' in kwargs['message'] else False
        uuid = kwargs.get('uuid', False)
        waiting = kwargs.get('waiting', False)
        is_welcome_message = kwargs.get('is_welcome_message', False)
        channel = request.env['mail.channel'].sudo().search([('uuid', '=', uuid)], limit=1)
        channel_id = channel.livechat_channel_id if channel.livechat_channel_id else False
        shortcode_obj = request.env['mail.shortcode'].sudo().search([])
        shortcode = False
        if channel_id.multi_chatbot == 'scripted_bot' and not is_welcome_message:
            for code_id in shortcode_obj:
                is_shortcode = str(message.lower()).find(code_id.source.lower())
                if is_shortcode != -1:
                    shortcode = code_id.substitution
        if waiting and channel_id.multi_chatbot == 'scripted_bot':
            msg = "<p>" + str(channel_id.default_message) + "</p>" if channel_id.default_message else "<p> Hello, How Are You!</p>"
            mes_ex = Message.sudo().create({'body':msg,
                            'channel_ids':[(6, 0, [channel.id])],
                            'record_name': 'USER BOT',
                            'message_type':'comment',
                            'model':'mail.channel',
                            'res_id':channel.id
                            })
        
        if not shortcode and ConfigOBJ and channel.helpdesk_lead_id.status in ['new']:
            c_company = request.env.user.company_id
            chain_list = []
            for line in c_company.chain_of_bots:
                if line.chatbot and line.chatbot != channel_id.multi_chatbot:
                    chain_list.append(line.sequence)
            chain_list.sort()
            for sequence in chain_list:
                chain_bot_id = request.env['chain.bots'].sudo().search([('company_id','=',c_company.id),('sequence','=',sequence)])
                res = getattr(c_company, '%s_chain_response' % str(chain_bot_id.chatbot))(message)
                if res:
                    shortcode = res
                    break
        
        if not shortcode:
            shortcode = channel_id.bot_default_reply
        is_private_bot = True
        available_id = channel_id._get_available_users()
        if channel_id.is_private_bot:
            if request.website.user_id != request.env.user or available_id != request.env.user:
                is_private_bot = False
        
        if is_welcome_message:
            msg = "<p>" + str(message) + "</p>" if message else "<p> Hello, How Are You!</p>"
            author_id = request.env['res.partner'].sudo().browse(int(2))
            mes_ex = Message.sudo().create({'body':msg,
                        'channel_ids':[(6, 0, [channel.id])],
                        'record_name': 'USER BOT',
                        'author_id':author_id.id,
                        'message_type':'comment',
                        'model':'mail.channel',
                        'res_id':channel.id,
                        })
            if mes_ex:
                if mes_ex.author_id:
                    mes_ex.update({'email_from':mes_ex.author_id.email_formatted})
            return '<p>' + str(message) + '</p>'
        elif shortcode and channel_id and channel_id.multi_chatbot == 'scripted_bot' and is_private_bot and channel.helpdesk_lead_id.status in ['new'] and not waiting:
            author_id = request.env['res.partner'].sudo().browse(int(2))
            mes = Message.sudo().create({'body':'<p>' + str(shortcode) + '</p>',
                            'channel_ids':[(6, 0, [channel.id])],
                            'record_name': 'USER BOT',
                            'author_id':author_id.id,
                            'message_type':'comment',
                            'model':'mail.channel',
                            'res_id':channel.id,
                            })
            if mes:
                if mes.author_id:
                    mes.update({'email_from':mes.author_id.email_formatted})
            return '<p>' + str(shortcode) + '</p>'
        else:
            return False
    
    