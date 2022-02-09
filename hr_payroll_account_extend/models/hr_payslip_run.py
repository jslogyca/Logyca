# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    config_account = fields.Many2one('hr.payroll.account.config', string='Contabilidad', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    date_account = fields.Date('Date Account')
    move_payroll_id = fields.Many2one('account.move', string='Move Payroll')
    move_payroll_ss_id = fields.Many2one('account.move', string='Move Payroll SS')
    move_payroll_prov_id = fields.Many2one('account.move', string='Move Payroll Prov')

    def compute_account_payroll(self):
        if self.slip_ids and self.config_account:
            move_obj = self.create_move(self.config_account)
            self.write({'move_payroll_id': move_obj.id})

    def compute_account_payroll_ss(self):
        if self.slip_ids and self.config_account:
            move_obj = self.create_move_ss(self.config_account)
            self.write({'move_payroll_ss_id': move_obj.id})

    def compute_account_payroll_prov(self):
        if self.slip_ids and self.config_account:
            move_obj = self.create_move_prov(self.config_account)
            self.write({'move_payroll_prov_id': move_obj.id})

    def get_total_rule(self, rule_id):
        print('REGLAS', rule_id.ids)
        self._cr.execute(''' select coalesce(sum(l.total),'0.0')
                                from hr_payslip_line l
                                inner join hr_payslip p on p.id=l.slip_id
                                where p.payslip_run_id=%s and l.salary_rule_id in %s ''', (self.id, tuple(rule_id.ids)))
        total_rule = self._cr.fetchone()
        return total_rule[0]

    def create_move(self, config_account):
        if self.move_payroll_id and self.move_payroll_id.state=='posted':
            raise ValidationError('¡Error! El asiento de Nómina ya esta Publicado. "%s"' % self.move_payroll_id.name)
        if self.move_payroll_id and self.move_payroll_id.state=='draft':
            self.move_payroll_id.unlink()

        lines = []
        move_ids = self.env['account.move']
        total_debit = 0.0
        total_credit = 0.0
        for line in config_account.line_ids:
            if line.nature == 'credit':
                if line.by_cc:
                    self._cr.execute(''' select sum(l.total), g.name, e.budget_group_id, l.salary_rule_id
                                                from hr_payslip_line l
                                                inner join hr_payslip n on n.id=l.slip_id
                                                inner join hr_employee e on e.id=n.employee_id
                                                left join logyca_budget_group g on g.id=e.budget_group_id
                                                where l.salary_rule_id in %s and n.payslip_run_id=%s
                                                group by g.name, e.budget_group_id, l.salary_rule_id ''', (tuple(line.rule_ids.ids), self.id))
                    budget_line_ids = self._cr.fetchall()
                    if budget_line_ids:
                        for budget_line_id in budget_line_ids:
                            total_credit += payslip_line.total
                            lines.append((0, 0, {
                                'name': self.name,
                                'date': self.date_account,
                                'account_id': line.account_id.id,
                                'credit': budget_line_id[0],
                                'amount_currency': budget_line_id[0] * -1,  
                                'ref': self.name,
                                'partner_id': line.partner_id.id,
                                'company_id': self.company_id.id,
                                'date_maturity': self.date_account,
                                'journal_id': config_account.journal_id.id,
                                'x_budget_group': budget_line_id[2],
                            }))
                else:
                    if line.by_partner:
                        line_payslip_id = self.env['hr.payslip.line'].search([('slip_id.payslip_run_id', '=', self.id),('salary_rule_id', 'in', tuple(line.rule_ids.ids))])
                        if line_payslip_id:
                            for payslip_line in line_payslip_id:
                                total_credit += payslip_line.total
                                lines.append((0, 0, {
                                    'name': self.name,
                                    'date': self.date_account,
                                    'account_id': line.account_id.id,
                                    'credit': payslip_line.total,
                                    'amount_currency': payslip_line.total * -1,                                
                                    'ref': self.name,
                                    'partner_id': payslip_line.employee_id.address_home_id.id,
                                    'company_id': self.company_id.id,
                                    'date_maturity': self.date_account,
                                    'journal_id': config_account.journal_id.id,
                                }))                        
                    else:
                        if line.item_id:
                            for line_ss in line.item_id.item_ids:
                                total = line_ss.amount
                                total_credit += total
                                lines.append((0, 0, {
                                    'name': self.name,
                                    'date': self.date_account,
                                    'account_id': line.account_id.id,
                                    'credit': total,
                                    'amount_currency': total * -1,
                                    'ref': self.name,
                                    'partner_id': line_ss.partner_id.id,
                                    'company_id': self.company_id.id,
                                    'journal_id': config_account.journal_id.id,
                                    'date_maturity': self.date_account,
                                }))
                        else:
                            total = self.get_total_rule(line.rule_ids)
                            total_credit += total
                            lines.append((0, 0, {
                                'name': self.name,
                                'date': self.date_account,
                                'account_id': line.account_id.id,
                                'credit': total,
                                'amount_currency': total * -1,
                                'ref': self.name,
                                'partner_id': line.partner_id.id,
                                'company_id': self.company_id.id,
                                'journal_id': config_account.journal_id.id,
                                'date_maturity': self.date_account,
                            }))
            else:
                if line.by_cc:
                    self._cr.execute(''' select sum(l.total), g.name, e.budget_group_id, l.salary_rule_id
                                                from hr_payslip_line l
                                                inner join hr_payslip n on n.id=l.slip_id
                                                inner join hr_employee e on e.id=n.employee_id
                                                left join logyca_budget_group g on g.id=e.budget_group_id
                                                where l.salary_rule_id in %s and n.payslip_run_id=%s
                                                group by g.name, e.budget_group_id, l.salary_rule_id ''', (tuple(line.rule_ids.ids), self.id))
                    budget_line_ids = self._cr.fetchall()
                    if budget_line_ids:
                        for budget_line_id in budget_line_ids:
                            total_debit += budget_line_id[0]
                            lines.append((0, 0, {
                                'name': self.name,
                                'date': self.date_account,
                                'account_id': line.account_id.id,
                                'debit': budget_line_id[0],
                                'amount_currency': budget_line_id[0],                                
                                'ref': self.name,
                                'partner_id': line.partner_id.id,
                                'company_id': self.company_id.id,
                                'date_maturity': self.date_account,
                                'journal_id': config_account.journal_id.id,
                                'x_budget_group': budget_line_id[2],
                            }))
                else:
                    if line.by_partner:
                        line_payslip_id = self.env['hr.payslip.line'].search([('slip_id.payslip_run_id', '=', self.id),('salary_rule_id', 'in', tuple(line.rule_ids.ids))])
                        if line_payslip_id:
                            for payslip_line in line_payslip_id:
                                total_debit += payslip_line.total
                                lines.append((0, 0, {
                                    'name': self.name,
                                    'date': self.date_account,
                                    'account_id': line.account_id.id,
                                    'debit': payslip_line.total,
                                    'amount_currency': payslip_line.total,
                                    'ref': self.name,
                                    'partner_id': payslip_line.employee_id.address_home_id.id,
                                    'company_id': self.company_id.id,
                                    'date_maturity': self.date_account,
                                    'journal_id': config_account.journal_id.id,
                                }))                            
                    else:
                        if line.item_id:
                            for line_ss in line.item_id.item_ids:
                                total = line_ss.amount
                                total_debit += total
                                lines.append((0, 0, {
                                    'name': self.name,
                                    'date': self.date_account,
                                    'account_id': line.account_id.id,
                                    'debit': total,
                                    'amount_currency': total,
                                    'ref': self.name,
                                    'partner_id': line_ss.partner_id.id,
                                    'company_id': self.company_id.id,
                                    'date_maturity': self.date_account,
                                    'journal_id': config_account.journal_id.id,
                                }))
                        else:
                            total = self.get_total_rule(line.rule_ids)
                            total_debit += total
                            lines.append((0, 0, {
                                'name': self.name,
                                'date': self.date_account,
                                'account_id': line.account_id.id,
                                'debit': total,
                                'amount_currency': total,
                                'ref': self.name,
                                'partner_id': line.partner_id.id,
                                'company_id': self.company_id.id,
                                'date_maturity': self.date_account,
                                'journal_id': config_account.journal_id.id,
                            }))
        print('111111111', total_debit, total_credit)
        if total_debit > total_credit:
            lines.append((0, 0, {
                'name': self.name,
                'date': self.date_account,
                'account_id': 350,
                'credit': abs(total_debit-total_credit),
                'amount_currency': abs((total_debit-total_credit)) * -1,
                'ref': self.name,
                'partner_id': 9882,
                'company_id': self.company_id.id,
                'journal_id': config_account.journal_id.id,
                'date_maturity': self.date_account,
            }))
        else:
            lines.append((0, 0, {
                'name': self.name,
                'date': self.date_account,
                'account_id': 350,
                'debit': abs(total_debit-total_credit),
                'amount_currency': abs(total_debit-total_credit),
                'ref': self.name,
                'partner_id': 9882,
                'company_id': self.company_id.id,
                'date_maturity': self.date_account,
                'journal_id': config_account.journal_id.id,
            }))            
        move_obj = move_ids.create({
            'type': 'entry',
            'partner_id': self.company_id.partner_id.id,
            'journal_id': self.config_account.journal_id.id,
            'ref': self.name,
            'date': self.date_account,
            'company_id': self.company_id.id,
            'line_ids': lines,
            'currency_id': self.company_id.currency_id.id,
        })
        return move_obj

    def create_move_ss(self, config_account):
        if self.move_payroll_ss_id and self.move_payroll_ss_id.state=='posted':
            raise ValidationError('¡Error! El asiento de Nómina ya esta Publicado. "%s"' % self.move_payroll_ss_id.name)
        if self.move_payroll_ss_id and self.move_payroll_ss_id.state=='draft':
            self.move_payroll_ss_id.unlink()

        lines = []
        move_ids = self.env['account.move']
        total_debit = 0.0
        total_credit = 0.0
        for line in config_account.line_ss_ids:
            if line.nature == 'credit':
                if line.by_cc:
                    self._cr.execute(''' select sum(l.total), g.name, e.budget_group_id, l.salary_rule_id
                                                from hr_payslip_line l
                                                inner join hr_payslip n on n.id=l.slip_id
                                                inner join hr_employee e on e.id=n.employee_id
                                                left join logyca_budget_group g on g.id=e.budget_group_id
                                                where l.salary_rule_id in %s and n.payslip_run_id=%s
                                                group by g.name, e.budget_group_id, l.salary_rule_id ''', (tuple(line.rule_ids.ids), self.id))
                    budget_line_ids = self._cr.fetchall()
                    if budget_line_ids:
                        for budget_line_id in budget_line_ids:
                            total_credit += payslip_line.total
                            lines.append((0, 0, {
                                'name': self.name,
                                'date': self.date_account,
                                'account_id': line.account_id.id,
                                'credit': budget_line_id[0],
                                'amount_currency': budget_line_id[0] * -1,  
                                'ref': self.name,
                                'partner_id': line.partner_id.id,
                                'company_id': self.company_id.id,
                                'date_maturity': self.date_account,
                                'journal_id': config_account.journal_ss_id.id,
                                'x_budget_group': budget_line_id[2],
                            }))
                else:
                    if line.by_partner:
                        line_payslip_id = self.env['hr.payslip.line'].search([('slip_id.payslip_run_id', '=', self.id),('salary_rule_id', 'in', tuple(line.rule_ids.ids))])
                        if line_payslip_id:
                            for payslip_line in line_payslip_id:
                                total_credit += payslip_line.total
                                lines.append((0, 0, {
                                    'name': self.name,
                                    'date': self.date_account,
                                    'account_id': line.account_id.id,
                                    'credit': payslip_line.total,
                                    'amount_currency': payslip_line.total * -1,                                
                                    'ref': self.name,
                                    'partner_id': payslip_line.employee_id.address_home_id.id,
                                    'company_id': self.company_id.id,
                                    'date_maturity': self.date_account,
                                    'journal_id': config_account.journal_ss_id.id,
                                }))                        
                    else:
                        if line.item_id:
                            for line_ss in line.item_id.item_ids:
                                total = line_ss.amount
                                total_credit += total
                                lines.append((0, 0, {
                                    'name': self.name,
                                    'date': self.date_account,
                                    'account_id': line.account_id.id,
                                    'credit': total,
                                    'amount_currency': total * -1,
                                    'ref': self.name,
                                    'partner_id': line_ss.partner_id.id,
                                    'company_id': self.company_id.id,
                                    'journal_id': config_account.journal_ss_id.id,
                                    'date_maturity': self.date_account,
                                }))
                        else:
                            total = self.get_total_rule(line.rule_ids)
                            total_credit += total
                            lines.append((0, 0, {
                                'name': self.name,
                                'date': self.date_account,
                                'account_id': line.account_id.id,
                                'credit': total,
                                'amount_currency': total * -1,
                                'ref': self.name,
                                'partner_id': line.partner_id.id,
                                'company_id': self.company_id.id,
                                'journal_id': config_account.journal_ss_id.id,
                                'date_maturity': self.date_account,
                            }))
            else:
                if line.by_cc:
                    if line.amount:
                        self._cr.execute(''' select count(e.id), g.name, e.budget_group_id
                                                    from hr_payslip n
                                                    inner join hr_employee e on e.id=n.employee_id
                                                    left join logyca_budget_group g on g.id=e.budget_group_id
                                                    where n.payslip_run_id=%s
                                                    group by g.name, e.budget_group_id ''', (self.id,))
                    else:
                        self._cr.execute(''' select sum(l.total), g.name, e.budget_group_id, l.salary_rule_id
                                                    from hr_payslip_line l
                                                    inner join hr_payslip n on n.id=l.slip_id
                                                    inner join hr_employee e on e.id=n.employee_id
                                                    left join logyca_budget_group g on g.id=e.budget_group_id
                                                    where l.salary_rule_id in %s and n.payslip_run_id=%s
                                                    group by g.name, e.budget_group_id, l.salary_rule_id ''', (tuple(line.rule_ids.ids), self.id))
                    budget_line_ids = self._cr.fetchall()
                    if budget_line_ids:
                        for budget_line_id in budget_line_ids:
                            print('12121212121212121', budget_line_id, total_debit)
                            if line.amount > 0.0:
                                self._cr.execute(''' select count(*)
                                                            from hr_payslip
                                                            where payslip_run_id=%s ''', (self.id,))
                                total_payslip = self._cr.fetchone()
                                total_line = round(((line.amount*budget_line_id[0])/total_payslip[0]),2)
                            else:
                                total_line = budget_line_id[0]
                            total_debit += total_line
                            lines.append((0, 0, {
                                'name': self.name,
                                'date': self.date_account,
                                'account_id': line.account_id.id,
                                'debit': total_line,
                                'amount_currency': total_line,
                                'ref': self.name,
                                'partner_id': line.partner_id.id,
                                'company_id': self.company_id.id,
                                'date_maturity': self.date_account,
                                'journal_id': config_account.journal_ss_id.id,
                                'x_budget_group': budget_line_id[2],
                            }))
                else:
                    if line.by_partner:
                        line_payslip_id = self.env['hr.payslip.line'].search([('slip_id.payslip_run_id', '=', self.id),('salary_rule_id', 'in', tuple(line.rule_ids.ids))])
                        if line_payslip_id:
                            for payslip_line in line_payslip_id:
                                total_debit += payslip_line.total
                                lines.append((0, 0, {
                                    'name': self.name,
                                    'date': self.date_account,
                                    'account_id': line.account_id.id,
                                    'debit': payslip_line.total,
                                    'amount_currency': payslip_line.total,
                                    'ref': self.name,
                                    'partner_id': payslip_line.employee_id.address_home_id.id,
                                    'company_id': self.company_id.id,
                                    'date_maturity': self.date_account,
                                    'journal_id': config_account.journal_ss_id.id,
                                }))                            
                    else:
                        if line.item_id:
                            for line_ss in line.item_id.item_ids:
                                total = line_ss.amount
                                total_debit += total
                                lines.append((0, 0, {
                                    'name': self.name,
                                    'date': self.date_account,
                                    'account_id': line.account_id.id,
                                    'debit': total,
                                    'amount_currency': total,
                                    'ref': self.name,
                                    'partner_id': line_ss.partner_id.id,
                                    'company_id': self.company_id.id,
                                    'date_maturity': self.date_account,
                                    'journal_id': config_account.journal_ss_id.id,
                                }))
                        else:
                            total = self.get_total_rule(line.rule_ids)
                            total_debit += total
                            lines.append((0, 0, {
                                'name': self.name,
                                'date': self.date_account,
                                'account_id': line.account_id.id,
                                'debit': total,
                                'amount_currency': total,
                                'ref': self.name,
                                'partner_id': line.partner_id.id,
                                'company_id': self.company_id.id,
                                'date_maturity': self.date_account,
                                'journal_id': config_account.journal_ss_id.id,
                            }))
        print('111111111', total_debit, total_credit)
        if total_debit > total_credit:
            print('44444444', total_debit, total_credit, abs((total_debit-total_credit)))
            lines.append((0, 0, {
                'name': self.name,
                'date': self.date_account,
                'account_id': config_account.account_id.id,
                'credit': abs(round(total_debit-total_credit,2)),
                'amount_currency': abs((total_debit-total_credit)) * -1,
                'ref': self.name,
                'partner_id': 9882,
                'company_id': self.company_id.id,
                'journal_id': config_account.journal_ss_id.id,
                'date_maturity': self.date_account,
            }))
        else:
            lines.append((0, 0, {
                'name': self.name,
                'date': self.date_account,
                'account_id': config_account.account_id.id,
                'debit': abs(round(total_debit-total_credit,2)),
                'amount_currency': abs(total_debit-total_credit),
                'ref': self.name,
                'partner_id': 9882,
                'company_id': self.company_id.id,
                'date_maturity': self.date_account,
                'journal_id': config_account.journal_ss_id.id,
            }))            
        move_obj = move_ids.create({
            'type': 'entry',
            'partner_id': self.company_id.partner_id.id,
            'journal_id': self.config_account.journal_ss_id.id,
            'ref': self.name,
            'date': self.date_account,
            'company_id': self.company_id.id,
            'line_ids': lines,
            'currency_id': self.company_id.currency_id.id,
        })
        return move_obj

    def create_move_prov(self, config_account):
        if self.move_payroll_prov_id and self.move_payroll_prov_id.state=='posted':
            raise ValidationError('¡Error! El asiento de Nómina ya esta Publicado. "%s"' % self.move_payroll_prov_id.name)
        if self.move_payroll_prov_id and self.move_payroll_prov_id.state=='draft':
            self.move_payroll_prov_id.unlink()

        lines = []
        move_ids = self.env['account.move']
        total_debit = 0.0
        total_credit = 0.0
        for line in config_account.line_prov_ids:
            if line.nature == 'credit':
                if line.by_cc:
                    self._cr.execute(''' select sum(l.total), g.name, e.budget_group_id, l.salary_rule_id
                                                from hr_payslip_line l
                                                inner join hr_payslip n on n.id=l.slip_id
                                                inner join hr_employee e on e.id=n.employee_id
                                                left join logyca_budget_group g on g.id=e.budget_group_id
                                                where l.salary_rule_id in %s and n.payslip_run_id=%s
                                                group by g.name, e.budget_group_id, l.salary_rule_id ''', (tuple(line.rule_ids.ids), self.id))
                    budget_line_ids = self._cr.fetchall()
                    if budget_line_ids:
                        for budget_line_id in budget_line_ids:
                            total_credit += payslip_line.total
                            lines.append((0, 0, {
                                'name': self.name,
                                'date': self.date_account,
                                'account_id': line.account_id.id,
                                'credit': budget_line_id[0],
                                'amount_currency': budget_line_id[0] * -1,  
                                'ref': self.name,
                                'partner_id': line.partner_id.id,
                                'company_id': self.company_id.id,
                                'date_maturity': self.date_account,
                                'journal_id': config_account.journal_prov_id.id,
                                'x_budget_group': budget_line_id[2],
                            }))
                else:
                    if line.by_partner:
                        line_payslip_id = self.env['hr.payslip.line'].search([('slip_id.payslip_run_id', '=', self.id),('salary_rule_id', 'in', tuple(line.rule_ids.ids))])
                        if line_payslip_id:
                            for payslip_line in line_payslip_id:
                                total_credit += payslip_line.total
                                lines.append((0, 0, {
                                    'name': self.name,
                                    'date': self.date_account,
                                    'account_id': line.account_id.id,
                                    'credit': payslip_line.total,
                                    'amount_currency': payslip_line.total * -1,                                
                                    'ref': self.name,
                                    'partner_id': payslip_line.employee_id.address_home_id.id,
                                    'company_id': self.company_id.id,
                                    'date_maturity': self.date_account,
                                    'journal_id': config_account.journal_prov_id.id,
                                }))                        
                    else:
                        if line.item_id:
                            for line_ss in line.item_id.item_ids:
                                total = line_ss.amount
                                total_credit += total
                                lines.append((0, 0, {
                                    'name': self.name,
                                    'date': self.date_account,
                                    'account_id': line.account_id.id,
                                    'credit': total,
                                    'amount_currency': total * -1,
                                    'ref': self.name,
                                    'partner_id': line_ss.partner_id.id,
                                    'company_id': self.company_id.id,
                                    'journal_id': config_account.journal_prov_id.id,
                                    'date_maturity': self.date_account,
                                }))
                        else:
                            total = self.get_total_rule(line.rule_ids)
                            total_credit += total
                            lines.append((0, 0, {
                                'name': self.name,
                                'date': self.date_account,
                                'account_id': line.account_id.id,
                                'credit': total,
                                'amount_currency': total * -1,
                                'ref': self.name,
                                'partner_id': line.partner_id.id,
                                'company_id': self.company_id.id,
                                'journal_id': config_account.journal_prov_id.id,
                                'date_maturity': self.date_account,
                            }))
            else:
                if line.by_cc:
                    self._cr.execute(''' select sum(l.total), g.name, e.budget_group_id, l.salary_rule_id
                                                from hr_payslip_line l
                                                inner join hr_payslip n on n.id=l.slip_id
                                                inner join hr_employee e on e.id=n.employee_id
                                                left join logyca_budget_group g on g.id=e.budget_group_id
                                                where l.salary_rule_id in %s and n.payslip_run_id=%s
                                                group by g.name, e.budget_group_id, l.salary_rule_id ''', (tuple(line.rule_ids.ids), self.id))
                    budget_line_ids = self._cr.fetchall()
                    if budget_line_ids:
                        for budget_line_id in budget_line_ids:
                            total_debit += budget_line_id[0]
                            lines.append((0, 0, {
                                'name': self.name,
                                'date': self.date_account,
                                'account_id': line.account_id.id,
                                'debit': budget_line_id[0],
                                'amount_currency': budget_line_id[0],                                
                                'ref': self.name,
                                'partner_id': line.partner_id.id,
                                'company_id': self.company_id.id,
                                'date_maturity': self.date_account,
                                'journal_id': config_account.journal_prov_id.id,
                                'x_budget_group': budget_line_id[2],
                            }))
                else:
                    if line.by_partner:
                        line_payslip_id = self.env['hr.payslip.line'].search([('slip_id.payslip_run_id', '=', self.id),('salary_rule_id', 'in', tuple(line.rule_ids.ids))])
                        if line_payslip_id:
                            for payslip_line in line_payslip_id:
                                total_debit += payslip_line.total
                                lines.append((0, 0, {
                                    'name': self.name,
                                    'date': self.date_account,
                                    'account_id': line.account_id.id,
                                    'debit': payslip_line.total,
                                    'amount_currency': payslip_line.total,
                                    'ref': self.name,
                                    'partner_id': payslip_line.employee_id.address_home_id.id,
                                    'company_id': self.company_id.id,
                                    'date_maturity': self.date_account,
                                    'journal_id': config_account.journal_prov_id.id,
                                }))                            
                    else:
                        if line.item_id:
                            for line_ss in line.item_id.item_ids:
                                total = line_ss.amount
                                total_debit += total
                                lines.append((0, 0, {
                                    'name': self.name,
                                    'date': self.date_account,
                                    'account_id': line.account_id.id,
                                    'debit': total,
                                    'amount_currency': total,
                                    'ref': self.name,
                                    'partner_id': line_ss.partner_id.id,
                                    'company_id': self.company_id.id,
                                    'date_maturity': self.date_account,
                                    'journal_id': config_account.journal_prov_id.id,
                                }))
                        else:
                            total = self.get_total_rule(line.rule_ids)
                            total_debit += total
                            lines.append((0, 0, {
                                'name': self.name,
                                'date': self.date_account,
                                'account_id': line.account_id.id,
                                'debit': total,
                                'amount_currency': total,
                                'ref': self.name,
                                'partner_id': line.partner_id.id,
                                'company_id': self.company_id.id,
                                'date_maturity': self.date_account,
                                'journal_id': config_account.journal_prov_id.id,
                            }))
        print('111111111', total_debit, total_credit)
        if total_debit > total_credit:
            lines.append((0, 0, {
                'name': self.name,
                'date': self.date_account,
                'account_id': config_account.account_id.id,
                'credit': abs(total_debit-total_credit),
                'amount_currency': abs((total_debit-total_credit)) * -1,
                'ref': self.name,
                'partner_id': 9882,
                'company_id': self.company_id.id,
                'journal_id': config_account.journal_prov_id.id,
                'date_maturity': self.date_account,
            }))
        else:
            lines.append((0, 0, {
                'name': self.name,
                'date': self.date_account,
                'account_id': config_account.account_id.id,
                'debit': abs(total_debit-total_credit),
                'amount_currency': abs(total_debit-total_credit),
                'ref': self.name,
                'partner_id': 9882,
                'company_id': self.company_id.id,
                'date_maturity': self.date_account,
                'journal_id': config_account.journal_prov_id.id,
            }))            
        move_obj = move_ids.create({
            'type': 'entry',
            'partner_id': self.company_id.partner_id.id,
            'journal_id': self.config_account.journal_prov_id.id,
            'ref': self.name,
            'date': self.date_account,
            'company_id': self.company_id.id,
            'line_ids': lines,
            'currency_id': self.company_id.currency_id.id,
        })
        return move_obj
