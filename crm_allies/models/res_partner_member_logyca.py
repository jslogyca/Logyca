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
    vat = fields.Char(string='NIT')
    name = fields.Char(string='Name')
    x_type_vinculation = fields.Many2one('logyca.vinculation_types', string='Tipo de vinculación')
    type_member = fields.Selection([("A", "TIPO A"), 
                                ("B", "TIPO B"),
                                ("C", "TIPO C")], string='Clasificación')
    member_red_id = fields.Many2one('logyca.member.red', string='Red de Valor')
    x_sector_id = fields.Many2one('logyca.sectors', string='Sector')
    city_id = fields.Many2one('logyca.city', string='Ciudad')
    x_date_vinculation = fields.Date('Fecha de Vinculación')
    meet_loyalty = fields.Selection([("SI", "SI"),
                                ("NO", "NO")], default="COMERCIAL", string='Reunión Fidelización')    
    date_loyalty = fields.Date(string='Fecha de Fidelización')
    description_loyalty = fields.Char('Obsercaciones Fidelización')
    service_member_count = fields.Integer(compute='_compute_service_member_count', string='Servicios Count')
    benefit_member_count = fields.Integer(compute='_compute_service_member_count', string='Benficios Count')
    x_company_size = fields.Selection([("1", "Mipyme"), 
                                ("2", "Pyme"),
                                ("3", "Mediana"),
                                ("4", "Grande"),
                                ("5", "Micro"),
                                ("6", "Pequeña")], string='Tamaño')

    def _select(self):
        select_str = """
        SELECT
            p.id as id, 
            p.id as partner_id,
            p.vat as vat,
            p.name || ' - ' || p.vat || ' - ' || vp.name as name,
            vp.id as x_type_vinculation,
            p.type_member as type_member,
            p.member_red_id as member_red_id,
            p.x_city as city_id,
            to_char(p.x_date_vinculation,'YYYY/MM/DD') AS x_date_vinculation,
            p.x_sector_id as x_sector_id,
            p.meet_loyalty as meet_loyalty,
            p.date_loyalty as date_loyalty,
            p.description_loyalty as description_loyalty,
            1 as sale_order_count,
            p.x_company_size as x_company_size
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

    def action_view_service_member(self):
        action = self.env['ir.actions.act_window']._for_xml_id('crm_allies.action_member_product_logyca_partner')
        all_child = self.with_context(active_test=False).search([('partner_id', 'child_of', self.ids)])
        action["domain"] = [("partner_id", "in", all_child.ids)]
        return action

    def action_view_benefit_member(self):
        action = self.env['ir.actions.act_window']._for_xml_id('crm_allies.action_benefits_membership_partner')
        all_child = self.with_context(active_test=False).search([('partner_id', 'child_of', self.ids)])
        action["domain"] = [("partner_id", "in", all_child.ids)]
        return action

    def _compute_service_member_count(self):
        member_product_id = self.env['res.member.product.logyca'].search([('partner_id', '=', self.partner_id.id)], 
                    order="id asc")
        member_benefit_id = self.env['benefits.membership.partner'].search([('partner_id', '=', self.partner_id.id),
                                                ('date_done', '>=', '2025-01-01'),
                                                ('date_done', '<=', '2025-12-31')], 
                    order="id asc")
        (self).service_member_count = len(member_product_id)
        (self).benefit_member_count = len(member_benefit_id)
