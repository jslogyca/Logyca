# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class HRSalaryRuleCategory(models.Model):
    _inherit = "hr.salary.rule.category"

    const_config = fields.Boolean('Constant Config', default=False)
