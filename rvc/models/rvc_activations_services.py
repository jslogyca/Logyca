from odoo import models
from .enums import SkuRvcProductsEnum
from typing import Tuple, List

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

        product = self.env['product.product'].search([
            ('name', 'ilike', 'colabora'),
            ('attribute_value_ids', 'like', f'nivel {postulation.colabora_level}')
        ])

        if product:
            return product.id
        return 0
