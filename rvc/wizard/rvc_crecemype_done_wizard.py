# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import date_utils

import base64
import json
import re
import requests
import logging
import uuid
import textwrap
import time


class RVCCrecemypeDoneWizard(models.TransientModel):
    _name = 'rvc.crecemype.done.wizard'
    _description = 'RVC Crecemype Done Wizard'

    date_done_cons = fields.Date(string='Date Solución', default=fields.Date.context_today)

    def action_application_done(self):
        active_id = self.env.context.get('active_id')
        context = dict(self._context or {})
        if active_id:
            application_ids = self.env['benefit.application'].browse(context.get('active_ids'))
        for application_id in application_ids:
            application_id.write({'state': 'done', 'date_done_cons': self.date_done_cons})
            self.env.cr.commit()