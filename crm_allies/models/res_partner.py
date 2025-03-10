# -*- coding: utf-8 -*-

from odoo import api, fields, models, Command, _


class ResPartner(models.Model):
    _inherit = "res.partner"

    allies_logyca = fields.Boolean('Allies Logyca', default=False)
    team_allies = fields.Boolean('Logyca Team', default=False)
    allies_user_id = fields.Many2one('res.partner', domain="[('team_allies', '=', True)]")
    benefits_ids = fields.One2many('benefits.membership.partner', 'partner_id', string="Benefits", index=True)
    type_allies = fields.Selection([("ACADEMICOS", "ACADEMICOS"), 
                                ("COMERCIAL", "COMERCIAL"),
                                ("MASIFICACIÓN", "MASIFICACIÓN"),
                                ("MISIONALES", "MISIONALES")], default="COMERCIAL")
    sub_type_allies = fields.Selection([("CADENACOMERCIAL", "CADENA COMERCIAL"), 
                                ("CADENACOMERCIALDROGUERIAS", "CADENA COMERCIAL DROGUERIAS"),
                                ("CADENAINDEPENDIENTE", "CADENA INDEPENDIENTE"),
                                ("CONSUMOMASIVO", "CONSUMO MASIVO"),
                                ("GOBIERNO", "GOBIERNO"),
                                ("HARDDISCOUNT", "HARD DISCOUNT"),
                                ("ONG", "ONG"),
                                ("SERVICIOS", "SERVICIOS"),
                                ("UNIVERSIDAD", "UNIVERSIDAD"),
                                ("VARIOS", "VARIOS")])
    projects_ids = fields.One2many('project.allies', 'partner_id', string="Projects", index=True)
    type_member = fields.Selection([("A", "TIPO A"), 
                                ("B", "TIPO B"),
                                ("C", "TIPO C")], string='Clasificación')
    icon_id = fields.Many2one('ir.attachment', string='A', domain="[('name', '=', 'a.png')]")
    user_loyalty = fields.Boolean(string='Lider Fidelización')
    meet_loyalty = fields.Selection([("SI", "SI"),
                                ("NO", "NO")], default="NO", string='Reunión Fidelización')    
    date_loyalty = fields.Date(string='Fecha de Fidelización')
    follow_ids = fields.One2many('follow.partner.loyalty', 'partner_id', string="Fidelización", index=True)
    description_loyalty = fields.Char('Obsercaciones Fidelización')
