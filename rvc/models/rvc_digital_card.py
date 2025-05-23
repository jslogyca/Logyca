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
    contact_name = fields.Char('Nombre')
    contact_email = fields.Char('Email')
    contact_mobile = fields.Char('Teléfono')
    offered_service_id = fields.Many2one('rvc.digital.card.offered.service',
        string='Servicio', help="Servicio que ofrece la empresa")
    city_id = fields.Many2one('logyca.city', string='Ciudad')
    street = fields.Char('Dirección')
    url_website = fields.Char('Página Web')
    url_facebook = fields.Char('Facebook')
    url_instagram = fields.Char('Instagram')
    digital_card_img = fields.Binary('Tarjeta Digital Generada')
    digital_card_img_url = fields.Char('Link Tarjeta Digital')

    @api.depends('postulation_id')
    def _partner_name(self):
        for digital_card in self:
            digital_card.partner_name = digital_card.postulation_id.partner_id.partner_id.name

    def action_download(self):
        """ Allows to download the digital card image"""
        self.ensure_one()
        url = self.digital_card_img_url
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }
