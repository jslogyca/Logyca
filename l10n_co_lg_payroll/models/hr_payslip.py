# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def update_input_employee(self):
        if not self.contract_id:
            self.struct_id = False
        self.with_context(contract=True)._get_new_input_line_ids()
        self.with_context(contract=True)._onchange_worked_days_inputs()
        return

    def action_payslip_cancel_done(self):
        if self.filtered(lambda slip: slip.state == "done"):
            self.move_id.button_draft()
            # self.move_id.unlink()
        return self.write({"state": "cancel"})

    @api.model
    def _get_new_input_line_ids(self):
        if self.struct_id and self.struct_id.input_line_type_ids:
            # computation of the salary worked days
            input_line_id_values = self._get_input_line()
            input_lines_id = self.input_line_ids.browse([])
            for r in input_line_id_values:
                input_lines_id |= input_lines_id.new(r)
            if input_lines_id:
                self.update({'input_line_ids': input_lines_id})       

    def _get_input_line(self):
        res = []
        for input_lines in self.struct_id.input_line_type_ids:
            input_line = {
                'sequence': input_lines.sequence,
                'input_type_id': input_lines.id,
                'amount': 0.0,
            }
            res.append(input_line)
        return res