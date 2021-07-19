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
from odoo import api, fields, models, modules, tools

class ResCompanyRasa(models.Model):
    _inherit = 'res.company'
    
    def scripted_bot_chain_response(self,message_txt):
        bot_message = False
        if message_txt:
            shortcode_obj = self.env['mail.shortcode'].sudo().search([])
            for code_id in shortcode_obj:
                is_shortcode = str(message_txt.lower()).find(code_id.source.lower())
                if is_shortcode != -1:
                    bot_message = code_id.substitution
        return bot_message
    
class ImLivechatChannel(models.Model):
    _inherit = 'im_livechat.channel'
    
    multi_chatbot = fields.Selection(selection_add=[('scripted_bot', 'Scripted Bot')])
    is_private_bot = fields.Boolean('Private Chat (No Chatbot)')
    
    @api.onchange('multi_chatbot')
    def multi_chatbot_onchange(self):
        base = super(ImLivechatChannel, self).multi_chatbot_onchange()
        self.is_private_bot = False
        return base
    
class ChainOfBotsScriptedBot(models.Model):
    _inherit = 'chain.bots'
    
    chatbot = fields.Selection(selection_add=[('scripted_bot','Scripted Bot')])
    
    