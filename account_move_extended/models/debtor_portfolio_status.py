from odoo import _, api, fields, models

class debtorPortfolioStatus(models.Model):
    _name = 'debtor.portfolio.status'
    _description = 'Estado de Cartera'
    
    name = fields.Char('Nombre')
    code = fields.Char('Código')
    active = fields.Boolean('Activo', default=True)