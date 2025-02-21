# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)


class ResMemberRemovedLogyca(models.Model):
    _name = "res.member.removed.logyca"
    _auto = False
    _description = "Res Member Removed Logyca"

    id = fields.Integer('ID')
    partner_id = fields.Many2one('res.partner', 'Miembro', readonly=True)
    vat = fields.Char(string='NIT')
    x_type_vinculation = fields.Many2one('logyca.vinculation_types', string='Tipo de vinculación')
    type_member = fields.Selection([("A", "TIPO A"), 
                                ("B", "TIPO B"),
                                ("C", "TIPO C")], string='Clasificación')
    member_red_id = fields.Many2one('logyca.member.red', string='Red de Valor')
    x_sector_id = fields.Many2one('logyca.sectors', string='Sector')
    city_id = fields.Many2one('logyca.city', string='Ciudad')
    x_date_vinculation = fields.Date('Fecha de Vinculación')
    x_date_decoupling = fields.Date('Fecha de DesVinculación')
    x_reason_desvinculation = fields.Selection([('1', 'Desvinculado por no pago'), 
                                                ('2', 'Desvinculado Voluntariamente'),
                                                ('3', 'Desvinculado por Cesión y/o Fusión'),
                                                ('4', 'Desvinculado por Liquidación de la Empresa'),
                                                ('5', 'Desvinculado por mal uso del sistema'),
                                                ('6', 'Desvinculado por migración 2020')], string='Desvinculado por')
    x_reason_desvinculation_text = fields.Text(string='Observaciones desvinculación')

    def _select(self):
        select_str = """
        SELECT
            p.id as id, 
            p.id as partner_id,
            p.vat as vat,
            vp.id as x_type_vinculation,
            p.type_member as type_member,
            p.member_red_id as member_red_id,
            p.x_city as city_id,
            to_char(p.x_date_vinculation,'YYYY/MM/DD') AS x_date_vinculation,
            to_char(p.x_date_decoupling,'YYYY/MM/DD') AS x_date_decoupling,
            p.x_sector_id as x_sector_id,
            p.x_reason_desvinculation as x_reason_desvinculation,
            p.x_reason_desvinculation_text as x_reason_desvinculation_text
		"""
        return select_str


    def _from(self):

        from_str = """
            res_partner p
            INNER JOIN logyca_vinculation_types_res_partner_rel vpr on vpr.res_partner_id=p.id
            INNER JOIN logyca_vinculation_types vp on vp.id=vpr.logyca_vinculation_types_id
        """

        return from_str

    def _group_by(self):
        group_by_str = """
                WHERE vp.id in (1,11,20,22)
                AND p.x_date_decoupling between '2025-01-01' and '2025-12-31'
                ORDER BY vp.id DESC
        """
        return group_by_str


    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        sql = """CREATE or REPLACE VIEW %s as (
            %s
            FROM ( %s )
            %s
            )""" % (self._table, self._select(), self._from(), self._group_by())

        # _logger.info(sql)
        self.env.cr.execute(sql)