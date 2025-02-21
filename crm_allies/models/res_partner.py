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
    

    @api.onchange('x_type_vinculation', 'x_active_vinculation')
    def _onchange_type_vinculation(self):
        for partner_id in self:
            if partner_id.x_type_vinculation and partner_id.x_active_vinculation:
                for type_vinculation in partner_id.x_type_vinculation:
                        partner_id.category_id = [(6, 0, type_vinculation.tag_id.id)]

