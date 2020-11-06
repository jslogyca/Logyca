# -*- coding: utf-8 -*-

from odoo import tools
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

from functools import lru_cache

class InfoPartnerPowerBI(models.Model):
    _name = "partner.info.powerbi"
    _description = "Report - Info Contactos Power BI"
    _auto = False
    
    # Compañia
    nit = fields.Char(string='Nit', readonly=True)
    company = fields.Char(string='Compañia', readonly=True)
    x_active_vinculation = fields.Char(string='Activo', readonly=True)
    tipo_de_vinculacion = fields.Char(string='Tipo de vinculacion', readonly=True)
    vendedor = fields.Char(string='Vendedor', readonly=True)
    x_date_vinculation = fields.Date(string='Fecha de vinculación', readonly=True)
    telefono_cliente = fields.Char(string='Teléfono cliente', readonly=True)
    celular = fields.Char(string='Celular', readonly=True)
    street_company = fields.Char(string='Dirección', readonly=True)
    x_asset_range = fields.Char(string='Rango De Activos', readonly=True)
    x_sector_id = fields.Char(string='Sector', readonly=True)
    nombre_contacto = fields.Char(string='Contacto/Nombre', readonly=True)
    telefono_contacto = fields.Char(string='Contacto/Teléfono', readonly=True)
    tipe_contacto = fields.Char(string='Tipo De Contacto', readonly=True)
    create_date = fields.Date(string='Creado', readonly=True)
    active_contact = fields.Char(string='Contacto/Activo', readonly=True)
    job_title = fields.Char(string='Área & Cargo', readonly=True)
    email_contact = fields.Char(string='Contacto/Correo Electrónico ', readonly=True)
    x_not_contacted_again = fields.Integer(string='No volver a ser contactado', readonly=True)
    ubicacion_contact = fields.Char(string='Contacto/Ubicación', readonly=True)
    street = fields.Char(string='Dirección de contacto', readonly=True)
    
    @api.model
    def _select(self):
        #coalesce(e."x_studio_clase",'-') as clase,
        return '''
         select Row_Number() over (order by company) as ID,* from (
                select coalesce(a.vat,'-') as nit, 
                coalesce(a.display_name,'-') as company, 
                a.x_active_vinculation, 
                coalesce(v."name",'-') as tipo_de_vinculacion,
                coalesce(ven."name",'-') as vendedor,
                coalesce(a.x_date_vinculation,'1900-01-01') as x_date_vinculation,
                coalesce(a.mobile ,'-') as telefono_cliente,
                coalesce(a.phone,'-') as celular, 
                coalesce(a.street,'-') as street_company, 
                coalesce(r."name",'-') as x_asset_range,
                coalesce(s."name",'-')  as x_sector_id,
                coalesce(con."name",'-') as nombre_contacto,
                coalesce(con.phone ,'-')  ||' / '|| coalesce(con.mobile ,'-') as telefono_contacto,
                coalesce(ct."name",'-')  as tipe_contacto,
                coalesce(con.create_date,'1900-01-01') as create_date,
                coalesce(con.x_active_for_logyca,'0') as active_contact,
                -- contacto grupos de trabajo 
                coalesce(la."name",'-') ||' / '|| coalesce(jt."name",'-') as job_title,
                coalesce(con.email,'-') as email_contact,
                coalesce(con.x_not_contacted_again,'0') as x_not_contacted_again,
                coalesce(f."name",'-') ||' / '|| coalesce(h."name",'-') ||' / '|| coalesce(g."name",'-') as ubicacion_contact,
                coalesce(con.street,'-') as street
                From res_partner a
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
                ) as A 
                where  a.tipe_contacto <> 'Facturación Electrónica'
        ''' 

    def init(self):        
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW %s AS (
                %s 
            )
        ''' % (
            self._table, self._select()
        ))

    