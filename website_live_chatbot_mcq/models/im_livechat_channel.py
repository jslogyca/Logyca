# -*- coding: utf-8 -*-
###############################################################################
#
#   website_live_helpdesk for Odoo
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
from odoo import api, fields, models, _

class ImlivechatChannel(models.Model):
    _inherit = 'im_livechat.channel'
    
    source_question_id = fields.Many2one('mail.shortcode',related='issue_category.source_question_id',store=True)
    is_mcq_channel = fields.Boolean(string='Is MCQ Channel?',default=False)
    
    @api.onchange('multi_chatbot')
    def multi_chatbot_onchange(self):
        base = super(ImlivechatChannel, self).multi_chatbot_onchange()
        self.is_mcq_channel = False
        return base

class OnlineHelpCategory(models.Model):
    _inherit = 'online.help.category'
    
    source_question_id = fields.Many2one('mail.shortcode',string='Default Question')
    
class MailChannel(models.Model):
    _inherit = 'mail.channel'
    
    mcq_questions_ended = fields.Boolean(string="MCQ Questions Ended" ,default=False)
    
    