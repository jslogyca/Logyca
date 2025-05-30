# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError,ValidationError
from datetime import date

class AccountIncomeReport(models.TransientModel):
    _name = 'account.income.report'
    _description = 'Account Income Report'


    partner_id = fields.Many2one('res.partner', string='Partner')
    company_id = fields.Many2one('res.company','Compañía')
    sale_order = fields.Many2one('sale.order', string='Sale Order')
    name_order = fields.Char('Name Order')
    move_id = fields.Many2one('account.move','Invoice')
    name_move = fields.Char('Name Move')
    state = fields.Selection(selection=[('draft', 'Draft'),
                                    ('posted', 'Posted'),
                                    ('cancel', 'Cancelled')], string='Status', default='draft')
    invoice_date = fields.Date('Invoice Date')
    amount_invoice = fields.Float('Amount Invoice + Tax')
    amount_untaxed = fields.Float('Amount Invoice')
    asset_id = fields.Many2one('account.asset', string='Diferido')
    name_asset = fields.Char('Name Asset')
    move_dif_id = fields.Many2one('account.move','Mov. Diferido')
    name_dif_move = fields.Char('Name Dif. Move')
    amount_total = fields.Float('Amount Total')
    date = fields.Date('Diferido Date')
    state_dif = fields.Selection(selection=[('draft', 'Draft'),
                                    ('posted', 'Posted'),
                                    ('cancel', 'Cancelled')], string='Status Diferido', default='draft')
    id_usuario=fields.Integer('ID Usuario')


class WizardAccountIncomeReport(models.TransientModel):
    _name = 'wizard.account.income.report'
    _description = 'Wizard Account Income Report'

    date_start = fields.Date('Date Start')
    date_stop = fields.Date('Date Stop')


    def cargar_tabla(self):
        self.env['account.income.report'].search([('id_usuario','=',self._uid)]).unlink()
        consulta="""INSERT INTO account_income_report(partner_id, 
                                                    sale_order, 
                                                    name_order, 
                                                    move_id,
                                                    name_move,
                                                    state,
                                                    invoice_date,
                                                    amount_invoice,
                                                    amount_untaxed,
                                                    asset_id,
                                                    name_asset,
                                                    move_dif_id,
                                                    name_dif_move,
                                                    amount_total,
                                                    date,
                                                    state_dif,
                                                    company_id,
                                                    id_usuario,
                                                    create_uid,
                                                    create_date)

                    SELECT p.id, 
                            so.id,
                            so.name, 
                            m.id,
                            m.name,
                            m.state, 
                            m.date, 
                            m.amount_total, 
                            m.amount_untaxed, 
                            a.id,
                            a.name,
                            d.id,
                            d.name,
                            d.amount_total,
                            d.date,
                            d.state,
                            m.company_id,
                            """+str(self._uid)+""" as "id_usuario",
                            """+str(self._uid)+""",
                            now()
                    FROM sale_order so
                    inner join res_partner p on p.id=so.partner_id
                    inner join account_move m on m.invoice_origin=so.name
                    inner join account_move_line l on l.move_id=m.id
                    inner join account_asset a on a.id=l.asset_id
                    inner join account_move d on d.asset_id=a.id
                    where to_char(m.date,'yyyymmdd') between '"""+self.date_start.strftime('%Y%m%d')+"""'
                    and '"""+self.date_stop.strftime('%Y%m%d')+"""' and m.company_id = """+str(self.env.company.id)+"""
                    order by d.date asc """

        self.env.cr.execute(consulta)
        action = self.env.ref('account_reports_excel.action_account_income_report').read()[0]
        action['name']='Income'
        action['display_name']='Income'
        action['domain']=[('id_usuario','=',self._uid)]
        action['view_id']=self.env.ref('account_reports_excel.account_income_report_tree').id
        action['context']={'search_default_group_partner_id':1}
        return action                                    