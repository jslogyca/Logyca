# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)


class ReportCRMContact(models.Model):
    _name = "report.crm.contact"
    _auto = False
    _description = "Report CRM Contact"

    id = fields.Integer('ID')
    vat = fields.Char('NIT')
    partner_id = fields.Many2one('res.partner', 'EMPRESA', readonly=True)
    x_vinculation = fields.Boolean('ACTIVO')
    type_vinculacion_id = fields.Many2one('logyca.vinculation_types', 'TIPO DE VINCULACIÓN', readonly=True)
    sale_id = fields.Many2one('res.partner', 'VENDEDOR', readonly=True)
    x_date_vinculation = fields.Date('FECHA DE VINCULACIÓN')
    x_cargo_directivo = fields.Boolean('CARGO DIRECTIVO')
    phone = fields.Char('TELÉFONO')
    x_asset_range = fields.Many2one('logyca.asset_range', 'RANGO DE ACTIVOS', readonly=True)
    x_sector_id = fields.Many2one('logyca.sectors', 'SECTOR', readonly=True)
    contact_id = fields.Many2one('res.partner', 'CONTACTO/NOMBRE', readonly=True)
    phone_contact = fields.Char('CONTACTO/TÉLEFONO')
    type_contac = fields.Many2one('logyca.contact_types', 'CONTACTO/TIPO DE CONTACTO', readonly=True)
    type_contac_name = fields.Char('CONTACTO/TIPO DE CONTACTO NAME')
    create = fields.Datetime('CREADO')
    contact = fields.Boolean('CONTACTO/ACTIVO')
    job_title = fields.Many2one('logyca.areas', 'ÁREA & CARGO', readonly=True)
    email_contact = fields.Char('CONTACTO/CORREO ELECTRÓNICO')
    movil_contacto = fields.Char('MÓVIL DEL CONTACTO')
    x_not_contacted_again = fields.Boolean('NO VOLVER A SER CONTACTADO')
    ubicacion_contact = fields.Char('CONTACTO/UBICACIÓN')
    street = fields.Char('DIRECCIÓN DE CONTACTO')
    macro_sector = fields.Char('MACROSECTOR')
    x_company_size = fields.Selection([
                                        ('1', 'Mipyme'),
                                        ('2', 'Pyme'),
                                        ('3', 'Mediana'),
                                        ('4', 'Grande'),
                                        ('5', 'Micro'),
                                        ('6', 'Pequeña')
                                    ], string='TAMAÑO EMPRESA')
    revenue_memb_ids = fields.Many2one('revenue.macro.sector', 'RANGO DE INGRESOS', readonly=True)

    def _select(self):
        select_str = """
        SELECT
            a.id as id, 
            coalesce(a.vat,'-') as vat, 
            a.id as partner_id, 
            a.x_active_vinculation as x_vinculation,
            v.id as type_vinculacion_id,
            ven.id as sale_id,
            coalesce(a.x_date_vinculation,'1900-01-01') as x_date_vinculation,
            coalesce(con.x_cargo_directivo,'0') as x_cargo_directivo,
            coalesce(a.phone,'-') as phone, 
            r.id as x_asset_range,
            s.id  as x_sector_id,
            con.id as contact_id,
            con.phone as phone_contact,
            ct.id as type_contac,
            coalesce(ct."name",'-')  as type_contac_name,
            coalesce(con.create_date,'1900-01-01') as create,
            coalesce(con.x_active_for_logyca,'0') as contact,
            -- contacto grupos de trabajo 
            la.id as job_title,
            coalesce(con.email,'-') as email_contact,
            coalesce(con.mobile,'-') as movil_contacto, 
            coalesce(con.x_not_contacted_again,'0') as x_not_contacted_again,
            f.name as ubicacion_contact,
            coalesce(con.street,'-') as street,
            a.macro_sector as macro_sector,
            a.x_company_size as x_company_size,
            a.revenue_memb_ids as revenue_memb_ids
		"""
        return select_str


    def _from(self):

        from_str = """
            res_partner a
                --Tipo de tercero
                inner join logyca_type_thirdparty_res_partner_rel b on a.id = b.res_partner_id and b.logyca_type_thirdparty_id = 1
                inner join logyca_type_thirdparty tt on b.logyca_type_thirdparty_id = tt.id 
                --Tipo Vinculación
                left join logyca_vinculation_types_res_partner_rel vp on a.id = vp.res_partner_id 
                left join logyca_vinculation_types v on vp.logyca_vinculation_types_id = v.id 
                --Ubicación
                left join res_country c on A.country_id = C.id 
                left join logyca_city d on A.x_city = d.id 
                left join res_country_state E on A.state_id = E.Id
                --Rango Activos
                left join logyca_asset_range r on a.x_asset_range = r.id 
                --Sector
                left join logyca_sectors s on a.x_sector_id = s.id 
                --Contacto
                left join res_partner con on a.id = con.parent_id
                ----Ubicación Contacto
                left join res_country f on con.country_id = f.id 
                left join logyca_city g on con.x_city = g.id 
                left join res_country_state h on con.state_id = h.Id
                ----Tipo de contacto
                left join logyca_contact_types_res_partner_rel cr on con.id = cr.res_partner_id 
                left join logyca_contact_types ct on cr.logyca_contact_types_id = ct.id 
                ----Grupos de trabajo
                --left join logyca_work_groups_res_partner_rel wr on con.id =wr.res_partner_id 
                --left join logyca_work_groups w on wr.logyca_work_groups_id = w.id 
                ----Area y cargo
                left join logyca_areas la on con.x_contact_area = la.id 
                left join logyca_job_title jt on con.x_contact_job_title = jt.id 
                -- Usuario 
                left join res_users Usu on Usu.id = a.user_id 
                left join res_partner ven on ven.id = Usu.partner_id 
        """

        return from_str

    def _group_by(self):
        group_by_str = """
                WHERE ct.name <> 'Facturación Electrónica' OR ct.id is null
                ORDER BY a.id DESC
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