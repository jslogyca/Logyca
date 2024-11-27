from odoo import models
from .enums import SkuRvcProductsEnum
from typing import Tuple, List

class RvcActivationServices(models.Model):
    _name = 'rvc.activation.services'

    def calculate_sku(
        self, codes_quantity: int, gln_codes_quantity: int, invoice_codes_quantity: int
    ) -> Tuple[List[int], List[int]]:
        """Calculates the SKU and quantity for each type of code to be activated"""
        skus = []
        quantities = []

        if codes_quantity > 0:
            skus.append(SkuRvcProductsEnum.PRODUCT_CODES.value)
            quantities.append(codes_quantity)

        if gln_codes_quantity > 0:
            skus.append(SkuRvcProductsEnum.GLN_CODES.value)
            quantities.append(gln_codes_quantity)

        if invoice_codes_quantity > 0:
            skus.append(SkuRvcProductsEnum.INVOICE_CODES.value)
            quantities.append(invoice_codes_quantity)

        return (skus, quantities)
