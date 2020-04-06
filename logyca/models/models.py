# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

#--------------------------------Modelos propios de logyca------------------------------------#

# CIUDAD
class x_city(models.Model):
    _name = 'logyca.city'
    _description = 'Ciudades por departamento'

    state_id = fields.Many2one('res.country.state', string='Departamento', required=True)
    code = fields.Char(string='Código', size=10, required=True)
    name = fields.Char(string='Nombre', required=True)

# CIIU
class ciiu(models.Model):
    _name = 'logyca.ciiu'
    _parent_store = True
    _parent_name  = 'parent_id'
    _description = 'CIIU - Actividades economicas'

    code = fields.Char('Codigo', required=True)
    name = fields.Char('Name', required=True)
    porcent_ica = fields.Float(string='Porcentaje ICA')
    parent_id = fields.Many2one('logyca.ciiu','Parent Tag', ondelete='cascade')
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many('logyca.ciiu', 'parent_id', 'Child Tags')    
    
    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{}".format(record.name)))
        return result

# SECTORES
class x_sectors(models.Model):
    _name = 'logyca.sectors'
    _description = 'Sectores'

    code = fields.Char(string='Código', size=10,required=True)
    name = fields.Char(string='Nombre', required=True)

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} | {}".format(record.code, record.name)))
        return result

# TIPOS DE VINCULACION
class x_vinculation_types(models.Model):
    _name = 'logyca.vinculation_types'
    _description = 'Tipos de vinculación'

    code = fields.Char(string='Código', size=10, required=True)
    name = fields.Char(string='Nombre', size=100, required=True)
    active = fields.Boolean(string='Activo')
    novelty = fields.Selection([('1', 'Vigente'), ('2', 'No esta vigente para nuevos - se mantiene para las empresas que lo adquirieron')], string='Novedad', required=True)

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} | {}".format(record.code, record.name)))
        return result

# RESPONSABILIDADES RUT
class x_responsibilities_rut(models.Model):
    _name = 'logyca.responsibilities_rut'
    _description = 'Responsabilidades RUT'

    code = fields.Char(string='Identificador', size=5, required=True)
    description = fields.Char(string='Descripción', size=100, required=True)
    valid_for_fe = fields.Boolean(string='Valido para facturación electrónica')
    
    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} | {}".format(record.code, record.description)))
        return result

# TIPOS DE CONTACTO
class x_contact_types(models.Model):
    _name = 'logyca.contact_types'
    _description = 'Tipos de contacto'
    
    code = fields.Char(string='Código', size=10, required=True)
    name = fields.Char(string='Nombre', required=True)

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} | {}".format(record.code, record.name)))
        return result

# ÁREAS
class x_areas(models.Model):
    _name = 'logyca.areas'
    _description = 'Áreas'

    code = fields.Char(string='Código', size=10, required=True)
    name = fields.Char(string='Nombre', required=True)

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} | {}".format(record.code, record.name)))
        return result

# CARGOS
class x_job_title(models.Model):
    _name = 'logyca.job_title'
    _description = 'Cargos'

    area_id = fields.Many2one('logyca.areas', string='Área')
    code = fields.Char(string='Código', size=10, required=True)
    name = fields.Char(string='Nombre', required=True)

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} | {}".format(record.code, record.name)))
        return result

# GRUPOS DE TRABAJO
class x_work_groups(models.Model):
    _name = 'logyca.work_groups'
    _description = 'Grupos de Trabajo'

    code = fields.Char(string='Código', size=10, required=True)
    name = fields.Char(string='Nombre', required=True)

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} | {}".format(record.code, record.name)))
        return result

# TIPOS DE TERCERO
class x_type_thirdparty(models.Model):
    _name = 'logyca.type_thirdparty'
    _description = 'Tipos de tercero'
    
    code = fields.Char(string='Código', size=10, required=True)
    name = fields.Char(string='Nombre', required=True)
    types = fields.Selection([('1', 'Cliente / Cuenta'),
                              ('2', 'Contacto'),
                              ('3', 'Proveedor'),
                              ('4', 'Funcionario / Contratista')], string='Tipo', required=True)

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{}".format(record.name)))
        return result

class x_history_partner_notes(models.Model):
    _name = 'logyca.history_partner_notes'
    _description = 'Información historia de salesforce NOTAS'

    title = fields.Text(string='Titulo', required=True)
    activity_date = fields.Datetime(string='Fecha', required=True)
    body = fields.Text(string='Contenido', required=True)    
    
class x_history_partner_emails(models.Model):
    _name = 'logyca.history_partner_emails'
    _description = 'Información historia de salesforce EMAILS'

    title = fields.Text(string='Titulo', required=True)
    activity_date = fields.Datetime(string='Fecha', required=True)
    body = fields.Text(string='Contenido', required=True)    
    from_address = fields.Text(string='Desde')    
    to_address = fields.Text(string='Para')    
    cc_Address = fields.Text(string='Cc')    
    bcc_Address = fields.Text(string='Cco')    

#--------------------------------Modelos heredados de Odoo------------------------------------#

class ResCountry(models.Model):
    _inherit = 'res.country'
	
    x_code_dian = fields.Char(string='Código del país para la DIAN')

class ResCountryState(models.Model):
    _inherit = 'res.country.state'
	
    x_code_dian = fields.Char(string='Código de provincia/departamento para la DIAN')

class CRMTeam(models.Model):
    _inherit = 'crm.team'
	
    invoiced_target = fields.Float('Meta de Facturación',(12,0))
