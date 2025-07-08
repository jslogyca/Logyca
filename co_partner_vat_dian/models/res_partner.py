# -*- coding: utf-8 -*-
################################################################################
# Author      : Evolusie. (<https://Evolusie.com/>)
# Copyright(c): 2021-Present Evolusie.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#################################################################################
from odoo import api, fields, models

class ResPartner(models.Model):
    _inherit = "res.partner"

    def search_nit_dian(self):
        return{ 'type': 'ir.actions.act_url', 'url':'https://muisca.dian.gov.co/WebRutMuisca/DefConsultaEstadoRUT.faces','target': 'new'}
