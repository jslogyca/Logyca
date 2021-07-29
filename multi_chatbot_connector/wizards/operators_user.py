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
from odoo.exceptions import ValidationError

@api.model
def _lang_get(self):
    return self.env['res.lang'].get_installed()

class OperatorsUser(models.TransientModel):
    _name = 'operators.user'
    
    name = fields.Char("Name")
    user_ids = fields.One2many('operators.user.line','operators_id', string="Users")
    
    def action_add_user(self):
        user_check = self.env['operators.user.line'].sudo().search([('check_box','=',True),('id','in',self.user_ids.ids)])
        channel_id = self.env['im_livechat.channel'].sudo().browse(self._context.get('active_id'))
        if user_check:
            userlist = []
            for user in user_check:
                userlist.append(user.user_id.id)
            channel_id.user_ids = userlist
        else:
            raise ValidationError(_('Please Select Channel Category!'))
        
class OperatorsUserLine(models.TransientModel):
    _name = 'operators.user.line'
    
    check_box = fields.Boolean("Select")
    user_id = fields.Many2one('res.users','User')
    operators_id = fields.Many2one('operators.user','Operators')
    login = fields.Char('Login')
    language =  fields.Selection(_lang_get, string='Language')
    
    @api.onchange('user_id')
    def _onchange_user_id(self):
       self.login = self.user_id.login
       self.language = self.user_id.lang
    
    