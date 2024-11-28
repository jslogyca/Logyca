from odoo import models
from .enums import SkuRvcProductsEnum, ColaboraProductNameEnum
from typing import Tuple, List
import logging

class RvcActivationServices(models.AbstractModel):
    _name = 'rvc.activation.services'
    _description = 'Servicios de Activación RVC'

    def calculate_gs1_codes_sku(
        self, codes_quantity: int, glns_codes_quantity: int, invoice_codes_quantity: int
    ) -> Tuple[List[int], List[int]]:
        """Calculates the SKU and quantity for each type of code to be activated"""
        skus = []
        quantities = []

        if codes_quantity > 0:
            skus.append(SkuRvcProductsEnum.PRODUCT_CODES.value)
            quantities.append(codes_quantity)

        if glns_codes_quantity > 0:
            skus.append(SkuRvcProductsEnum.GLN_CODES.value)
            quantities.append(glns_codes_quantity)

        if invoice_codes_quantity > 0:
            skus.append(SkuRvcProductsEnum.INVOICE_CODES.value)
            quantities.append(invoice_codes_quantity)

        return (skus, quantities)

    def calculate_colabora_level_sku(
        self, postulation
    ) -> int:
        """Calculates the SKU for the level of colabora to be activated"""

        logging.debug("Starting calculate_colabora_level_sku with postulation: %s", postulation)

        product = self.env['product.product'].search([
            ('sale_ok', '=', True),
            ('product_tmpl_id.name', 'ilike', ColaboraProductNameEnum.COLABORA.value),
            ('product_template_variant_value_ids.name', 'ilike',
             f'nivel {postulation.colabora_level}')
        ], limit=1)

        logging.debug("Product search result: %s", product)

        if product:
            logging.debug("Product found with SKU: %s", product.id)
            return product.id
        else:
            raise ValueError("Producto colabora no encontrado para el nivel especificado.")
