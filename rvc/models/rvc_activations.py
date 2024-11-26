from odoo import _
import logging
import requests
from datetime import date
from .enums import OriginsEnum
from .dto import Order_InputDTO, OrderDetail_InputDTO, DigitalCard_InputDTO

def activate_logyca_colabora(postulation):
    """ Maps a rvc postulation into a logyca colabora activation request"""

    logging.debug("Activating Logyca Colabora for postulation %d", postulation.id)
    token = postulation.get_token_gs1_co_api()
    logging.debug("Token: %s", token)

    payload = {
        "nit": postulation.vat,
        "orderId": postulation.id,
        "sponsor": postulation.parent_id.vat,
        "digitalCards": [],
        "detailsOrder": [
            {
                "sku": "54",
                "quantity": 1,
                "totalDetailOrderValue": 0.0,
                "totalDetailOrderUnTaxed": 0.0
            }
        ],
        "buyerEmail": postulation.contact_email,
        "salesmanEmail": "",
        "totalOrderValue": 0,
        "totalOrderUnTaxed": 0,
        "origin": OriginsEnum.ODOO.value,
        "cellphone": postulation.contact_phone,
        "isSeller": postulation.is_seller
    }
    logging.info(" Postulation %d\nLogyca Colabora activation request: %s", postulation.id, payload)
    headers = {
        "Content-Type": "application",
        "Authorization": f"Bearer {token}" 
    }
    response = requests.post(
        "https://gateway-odoo-dev.azurewebsites.net/gateway/activator",
        json=payload,
        headers=headers,
        timeout=10)
    response_json = response.json()
    logging.info(
        "Postulation %d\nLogyca Colabora activation response: %s",
        postulation.id, response_json
    )

    postulation.message_post(
        body=_(f"Logyca Colabora activation response:\n{response_json}")
    )

    return True
