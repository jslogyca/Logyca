
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
from odoo import fields, models

class MailShortcodeRadioOptions(models.Model):
    _name = 'mail.shortcode.radio.options'
    
    name = fields.Char(string='Name',require=1)
    image = fields.Binary(string='Image')
    representation = fields.Selection([
                        ('text','Text'),
                        ('image','Image'),
                        ('text_image','Text + Image')
                    ],default='text',required=1)
    
class MailShortCodeRadioReply(models.Model):
    _name = 'mail.shortcode.radio.answers'
    
    answer_id = fields.Many2one('mail.shortcode.radio.options',string='Radio Option')
    next_question_id = fields.Many2one('mail.shortcode',string='Radio Reply Question')
    mail_source_id = fields.Many2one('mail.shortcode',string='Source Question')
    is_end_of_mcq = fields.Boolean(string='End of MCQ Questions',default=False)
    end_of_mcq_message = fields.Char('Questions Ended Message')

class MailShortcode(models.Model):
    _inherit = 'mail.shortcode'
    _rec_name = 'source'
    
    substitution_type = fields.Selection([
                            ('text','Text'),
                            ('radio','Radio')
                        ],string='Substitution Type',default='text',required=1)
    substitution = fields.Text('Substitution', required=False, index=True, help="The escaped html code replacing the shortcut")
    radio_answer_ids = fields.One2many('mail.shortcode.radio.answers','mail_source_id',string='Radio Answers Response')
    
    