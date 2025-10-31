# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date
import logging
_logger = logging.getLogger(__name__)


class AccountConsolidationWizard(models.TransientModel):
    _name = 'account.consolidation.wizard'
    _description = 'Wizard para Consolidación por Cuenta Contable'

    date_to = fields.Date(
        string='Fecha de Corte',
        required=True,
        default=fields.Date.context_today,
        help='Seleccione la fecha hasta la cual desea consolidar los valores'
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        default=lambda self: self.env.company,
        required=True
    )
    
    account_ids = fields.Many2many(
        'account.account',
        string='Cuentas Contables',
        help='Deje vacío para incluir todas las cuentas'
    )
    
    show_only_with_foreign_currency = fields.Boolean(
        string='Solo cuentas con moneda extranjera',
        default=False,
        help='Marque esta opción para mostrar solo cuentas con valores en moneda extranjera'
    )

    def action_generate_report(self):
        """Generar el reporte de consolidación con los filtros seleccionados"""
        self.ensure_one()
        
        # Construir el dominio de búsqueda
        domain = [('date_to', '<=', self.date_to)]
        
        if self.company_id:
            domain.append(('company_id', '=', self.company_id.id))
        
        if self.account_ids:
            domain.append(('account_id', 'in', self.account_ids.ids))
        
        if self.show_only_with_foreign_currency:
            domain.append(('total_amount_currency', '!=', 0))
        
        # Obtener los datos usando el método del modelo
        consolidation_model = self.env['account.consolidation.report']
        results = consolidation_model.get_consolidation_by_date(self.date_to)
        
        # Filtrar resultados según los criterios
        if self.account_ids:
            results = [r for r in results if r['account_id'] in self.account_ids.ids]
        
        if self.show_only_with_foreign_currency:
            results = [r for r in results if r['total_amount_currency'] != 0]
        
        # Retornar acción para mostrar los resultados
        return {
            'type': 'ir.actions.act_window',
            'name': f'Consolidación al {self.date_to.strftime("%d/%m/%Y")}',
            'res_model': 'account.consolidation.report',
            'view_mode': 'tree,pivot,graph',
            'domain': domain,
            'context': {
                'search_default_date_to': self.date_to,
                'default_date_to': self.date_to,
            },
            'target': 'current',
        }

    def action_export_to_excel(self):
        """Exportar el reporte a Excel"""
        self.ensure_one()
        
        # Obtener los datos
        consolidation_model = self.env['account.consolidation.report']
        results = consolidation_model.get_consolidation_by_date(self.date_to)
        
        # Filtrar resultados
        if self.account_ids:
            results = [r for r in results if r['account_id'] in self.account_ids.ids]
        
        if self.show_only_with_foreign_currency:
            results = [r for r in results if r['total_amount_currency'] != 0]
        
        # Aquí se puede implementar la exportación a Excel
        # usando xlsxwriter o una librería similar
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Exportación',
                'message': 'Funcionalidad de exportación a Excel en desarrollo',
                'type': 'warning',
                'sticky': False,
            }
        }
