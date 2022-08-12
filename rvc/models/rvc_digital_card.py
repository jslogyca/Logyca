from multiprocessing.spawn import old_main_modules
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class rvc_digital_card_offered_service(models.Model):
    _name = 'rvc.digital.card.offered.service'

    _description = """
        Servicios ofrecidos por la empresa
        que solicitó las tarjetas digitales.
    """

    name = fields.Char('name')
    active = fields.Boolean('active')

class rvc_digital_card(models.Model):
    _name = 'rvc.digital.card'

    _description = """
        Beneficio Tarjeta Digital (Digital Card)
        del programa RVC de LOGYCA
    """

    postulation_id = fields.Many2one('benefit.application','Postulación')
    name = fields.Char('name')
    qr_code = fields.Binary('QR')
    partner_name = fields.Char(compute="_partner_name",string='Empresa')
    partner_vat = fields.Char(related="postulation_id.vat",string='Num. Identificación')
    contact_name = fields.Char('Nombre Contacto')
    contact_email = fields.Char('Email Contacto')
    contact_mobile = fields.Char('contact_mobile') #TODO: poner widget: phone
    offered_service_id = fields.Many2one('rvc.digital.card.offered.service', string='Servicio que Ofrece')
    city_id = fields.Many2one('logyca.city', string='Ciudad')
    street = fields.Char('Dirección')
    url_website = fields.Char('Página Web') # TODO: poner widget: url
    url_facebook = fields.Char('Facebook') # TODO: poner widget: url
    url_instagram = fields.Char('Instagram') # TODO: poner widget: url
    digital_card_img = fields.Binary('Tarjeta Digital')

    @api.depends('postulation_id')
    def _partner_name(self):
        for digital_card in self:
            #TODO: probar la linea siguiente
            digital_card.partner_name = self.postulation_id.split('-')[0].strip()
