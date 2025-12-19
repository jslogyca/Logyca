# -*- coding: utf-8 -*-
from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    # Aprobadores por defecto para productos
    financial_approver_id = fields.Many2one(
        'res.users',
        string='Aprobador Financiero por Defecto',
        help='Usuario que aprobará por defecto las solicitudes de productos desde el punto de vista financiero'
    )
    
    legal_approver_id = fields.Many2one(
        'res.users',
        string='Aprobador Legal por Defecto',
        help='Usuario que aprobará por defecto las solicitudes de productos desde el punto de vista legal'
    )
    
    accounting_approver_id = fields.Many2one(
        'res.users',
        string='Aprobador Contable por Defecto',
        help='Usuario que aprobará por defecto las solicitudes de productos desde el punto de vista contable'
    )
    
    # Configuración de Anticipos
    financial_advance_approver_id = fields.Many2one(
        'res.users',
        string='Aprobador Financiero de Anticipos',
        help='Usuario que dará el visto bueno financiero a las solicitudes de anticipos'
    )
    
    advance_journal_id = fields.Many2one(
        'account.journal',
        string='Diario de Anticipos',
        help='Diario contable que se usará para causar los anticipos'
    )
    
    advance_cxp_account_id = fields.Many2one(
        'account.account',
        string='Cuenta CXP para Anticipos',
        help='Cuenta contable de Cuentas por Pagar (crédito)'
    )
    
    advance_cxc_account_id = fields.Many2one(
        'account.account',
        string='Cuenta CXC para Anticipos',
        help='Cuenta contable de Cuentas por Cobrar (débito) - Para terceros'
    )
    
    advance_cxc_employee_account_id = fields.Many2one(
        'account.account',
        string='Cuenta CXC para Anticipos de Empleados',
        help='Cuenta contable de Cuentas por Cobrar (débito) - Para empleados'
    )
    
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        
        # Aprobadores de productos
        financial_approver_id = ICPSudo.get_param(
            'analytic_account_request.default_financial_approver_id', default=False
        )
        legal_approver_id = ICPSudo.get_param(
            'analytic_account_request.default_legal_approver_id', default=False
        )
        accounting_approver_id = ICPSudo.get_param(
            'analytic_account_request.default_accounting_approver_id', default=False
        )
        
        # Configuración de anticipos
        financial_advance_approver_id = ICPSudo.get_param(
            'analytic_account_request.default_financial_advance_approver_id', default=False
        )
        advance_journal_id = ICPSudo.get_param(
            'analytic_account_request.advance_journal_id', default=False
        )
        advance_cxp_account_id = ICPSudo.get_param(
            'analytic_account_request.advance_cxp_account_id', default=False
        )
        advance_cxc_account_id = ICPSudo.get_param(
            'analytic_account_request.advance_cxc_account_id', default=False
        )
        advance_cxc_employee_account_id = ICPSudo.get_param(
            'analytic_account_request.advance_cxc_employee_account_id', default=False
        )
        
        res.update({
            'financial_approver_id': int(financial_approver_id) if financial_approver_id else False,
            'legal_approver_id': int(legal_approver_id) if legal_approver_id else False,
            'accounting_approver_id': int(accounting_approver_id) if accounting_approver_id else False,
            'financial_advance_approver_id': int(financial_advance_approver_id) if financial_advance_approver_id else False,
            'advance_journal_id': int(advance_journal_id) if advance_journal_id else False,
            'advance_cxp_account_id': int(advance_cxp_account_id) if advance_cxp_account_id else False,
            'advance_cxc_account_id': int(advance_cxc_account_id) if advance_cxc_account_id else False,
            'advance_cxc_employee_account_id': int(advance_cxc_employee_account_id) if advance_cxc_employee_account_id else False,
        })
        return res
    
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        
        # Aprobadores de productos
        ICPSudo.set_param(
            'analytic_account_request.default_financial_approver_id',
            self.financial_approver_id.id or False
        )
        ICPSudo.set_param(
            'analytic_account_request.default_legal_approver_id',
            self.legal_approver_id.id or False
        )
        ICPSudo.set_param(
            'analytic_account_request.default_accounting_approver_id',
            self.accounting_approver_id.id or False
        )
        
        # Configuración de anticipos
        ICPSudo.set_param(
            'analytic_account_request.default_financial_advance_approver_id',
            self.financial_advance_approver_id.id or False
        )
        ICPSudo.set_param(
            'analytic_account_request.advance_journal_id',
            self.advance_journal_id.id or False
        )
        ICPSudo.set_param(
            'analytic_account_request.advance_cxp_account_id',
            self.advance_cxp_account_id.id or False
        )
        ICPSudo.set_param(
            'analytic_account_request.advance_cxc_account_id',
            self.advance_cxc_account_id.id or False
        )
        ICPSudo.set_param(
            'analytic_account_request.advance_cxc_employee_account_id',
            self.advance_cxc_employee_account_id.id or False
        )
