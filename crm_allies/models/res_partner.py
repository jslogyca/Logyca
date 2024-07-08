# -*- coding: utf-8 -*-

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    allies_logyca = fields.Boolean('Allies Logyca', default=False)
    allies_user_id = fields.Many2one('res.partner')
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