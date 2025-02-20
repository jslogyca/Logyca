# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)


class ResPartnerMemberLogyca(models.Model):
    _name = "res.partner.member.logyca"
    _auto = False
    _description = "Res Partner Member Logyca"

    id = fields.Integer('ID')
    partner_id = fields.Many2one('res.partner', 'Miembro', readonly=True)
    x_type_vinculation = fields.Many2one('logyca.vinculation_types', string='Tipo de vinculación')
    type_member = fields.Selection([("A", "TIPO A"), 
                                ("B", "TIPO B"),
                                ("C", "TIPO C")], string='Clasificación')
    member_red_id = fields.Many2one('logyca.member.red', string='Red de Valor')
    city_id = fields.Many2one('logyca.city', string='Ciudad')
    x_date_vinculation = fields.Date('Fecha de Vinculación')

    def _select(self):
        select_str = """
        SELECT
            p.id as id, 
            p.id as partner_id,
            vp.id as x_type_vinculation,
            p.type_member as type_member,
            red.id as member_red_id,
            lc.id as city_id,
            to_char(p.x_date_vinculation,'YYYY/MM/DD') AS x_date_vinculation
		"""
        return select_str


    def _from(self):

        from_str = """
            res_partner p
            INNER JOIN logyca_vinculation_types_res_partner_rel vpr on vpr.res_partner_id=p.id
            INNER JOIN logyca_vinculation_types vp on vp.id=vpr.logyca_vinculation_types_id
            LEFT JOIN logyca_member_red red on red.id=p.member_red_id
            LEFT JOIN logyca_sectors s on s.id=p.x_sector_id
            LEFT JOIN logyca_city lc on lc.id=p.x_city
        """

        return from_str

    def _group_by(self):
        group_by_str = """
                WHERE vp.id in (1,11,20,22)
                AND p.x_active_vinculation IS True
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