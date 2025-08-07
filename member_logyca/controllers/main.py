from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleExtended(WebsiteSale):

    def values_postprocess(self, order, mode, values, errors, error_msg):
        new_values, errors, error_msg = super().values_postprocess(order, mode, values, errors, error_msg)

        # Agrega tus campos personalizados aquí
        new_values.update({
            'rango_type': values.get('rango_type'),
            'how_findout': values.get('how_findout'),
            'x_sector_id': int(values.get('x_sector_id')) if values.get('x_sector_id') else False,
        })

        return new_values, errors, error_msg