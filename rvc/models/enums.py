from enum import Enum

class OriginsEnum(Enum):
    """RVC Origins Enum"""
    ODOO = 'odoo'

class SkuRvcProductsEnum(Enum):
    """RVC Products Enum"""
    PRODUCT_CODES = 5
    GLN_CODES = 20
    INVOICE_CODES = 104
    DIGITAL_CARDS = 1671
