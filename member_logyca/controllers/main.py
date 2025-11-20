from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleExtended(WebsiteSale):

    def values_postprocess(self, order, mode, values, errors, error_msg):
        new_values, errors, error_msg = super().values_postprocess(order, mode, values, errors, error_msg)

        # Validación para rango_type 'other'
        if values.get('rango_type') == 'other':
            errors['rango_type'] = 'blocked'
            error_msg.append(' Aviso Importante: Este modelo está diseñado exclusivamente para microempresas, y tu compañía supera ese tamaño.  Te invitamos a agendar una sesión con nuestros asesores para conocer planes, tarifas y beneficios diseñados especialmente para las necesidades de tu empresa.')

        # Agrega tus campos personalizados aquí
        new_values.update({
            'rango_type': values.get('rango_type'),
            'how_findout': values.get('how_findout'),
            'x_sector_id': int(values.get('x_sector_id')) if values.get('x_sector_id') else False,
            'l10n_latam_identification_type_id': int(values.get('l10n_latam_identification_type_id')) if values.get('l10n_latam_identification_type_id') else False,
        })

        return new_values, errors, error_msg