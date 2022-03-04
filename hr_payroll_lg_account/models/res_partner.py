# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    type_reg_contribution = fields.Selection([('eps', 'EPS'), 
                                                ('fond_pens', 'Fondo de Pensiones'),
                                                ('fond_censa', 'Fondo de Cesantías'),
                                                ('arl', 'ARL'),
                                                ('caja', 'Caja de Compensación'),], string='Type Reg Contribution')

    