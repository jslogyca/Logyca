from odoo import models, _
import logging
import requests
from .rvc_activations_services import RvcActivationServices
from datetime import date
from .enums import OriginsEnum, SkuRvcProductsEnum
from .dto import Order_InputDTO, OrderDetail_InputDTO, DigitalCard_InputDTO
from odoo.exceptions import ValidationError, UserError

class RvcActivations(models.AbstractModel):
    _name = 'rvc.activations'
    _description = 'Activaciones RVC'

    def activate_logyca_colabora(self, postulation) -> bool:
        """Maps a rvc postulation into a logyca colabora activation request"""

        logging.debug("Activating Logyca / Colabora for postulation %d", postulation.id)
        # token = postulation.get_token_gs1_co_api()
        token = postulation.get_token_sso()
        logging.debug("Token: %s", token)

        colabora_level_sku = self.env['rvc.activation.services'] \
            .calculate_colabora_level_sku(postulation)

        order_input = Order_InputDTO(
            nit=postulation.vat,
            orderId=str(postulation.id),
            sponsor=postulation.parent_id.vat,
            digitalCards=[],
            detailsOrder=[
                OrderDetail_InputDTO(
                    sku=colabora_level_sku,
                    quantity=1,
                    totalDetailOrderValue=0.0,
                    totalDetailOrderUnTaxed=0.0
                )
            ],
            buyerEmail=postulation.contact_email,
            salesmanEmail="",
            totalOrderValue=0,
            totalOrderUnTaxed=0,
            origin=OriginsEnum.ODOO.value,
            cellphone=postulation.contact_phone,
            isSeller=postulation.is_seller
        )

        payload = order_input.model_dump()

        logging.info(
            " Postulation %d\nLogyca Colabora activation request: %s",
            postulation.id,
            payload,
        )

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }

        response = requests.post(
            "https://gateway-odoo-prod.azurewebsites.net/gateway/activator",
            json=payload,
            headers=headers,
            timeout=10,
        )

        if response.status_code == 200 and response.text.strip():
            response_json = response.json()
        else:
            raise ValidationError(f"Error en la activación: respuesta vacía o inválida del servicio. Código HTTP: {response.status_code}")

        logging.info(
            "Postulation %d\nLogyca Colabora activation response: %s",
            postulation.id,
            response_json
        )
        if response.status_code != 200:
            logging.error(
                "Postulation %d\nLogyca Colabora activation failed: %s",
                postulation.id,
                response_json
            )
            return False

        return True

    def activate_gs1_codes(self, postulation) -> bool:
        """Maps a rvc postulation into a gs1 codes activation request"""

        logging.debug("Activating GS1 Codes for postulation %d", postulation.id)
        token = postulation.get_token_sso()
        logging.debug("Token: %s", token)

        skus, quantities = self.env['rvc.activation.services'] \
            .calculate_gs1_codes_sku(
                postulation.codes_quantity,
                postulation.glns_codes_quantity,
                postulation.invoice_codes_quantity
        )

        details_order = []
        for sku, quantity in zip(skus, quantities):
            details_order.append(OrderDetail_InputDTO(
                sku=sku,
                quantity=quantity,
                totalDetailOrderValue=0.0,
                totalDetailOrderUnTaxed=0.0
            ))

        order_input = Order_InputDTO(
            nit=postulation.vat,
            orderId=str(postulation.id),
            sponsor=postulation.parent_id.vat,
            digitalCards=[],
            detailsOrder=details_order,
            buyerEmail=postulation.contact_email,
            salesmanEmail="",
            totalOrderValue=0,
            totalOrderUnTaxed=0,
            origin=OriginsEnum.ODOO.value,
            cellphone=postulation.contact_phone,
            isSeller=postulation.is_seller,
        )

        payload = order_input.model_dump()

        logging.info(
            " Postulation %d\nGS1 Codes activation request: %s", postulation.id, payload
        )

        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
        response = requests.post(
            "https://gateway-odoo-prod.azurewebsites.net/gateway/activator",
            json=payload,
            headers=headers,
            timeout=10,
        )

        response_json = response.json()
        logging.info(
            "Postulation %d\nGS1 Codes activation response: %s",
            postulation.id,
            response_json,
        )

        if response.status_code != 200:
            logging.error(
                "Postulation %d\nGS1 Codes activation failed: %s",
                postulation.id,
                response_json,
            )
            return False

        return True

    def activate_digital_cards(self, postulation) -> bool:
        """Maps a rvc postulation into a digital cards activation request"""

        logging.debug("Activating Digital Cards for postulation %d", postulation.id)
        # token = postulation.get_token_gs1_co_api()
        token = postulation.get_token_sso()
        logging.debug("Token: %s", token)

        digital_cards = []
        for card in postulation.digital_card_ids:
            digital_cards.append(
                DigitalCard_InputDTO(
                    name=card.contact_name,
                    email=card.contact_email,
                    phone=card.contact_mobile,
                    service=str(card.offered_service_id.id),
                    city=card.city_id.name,
                    address=card.street,
                    website=card.url_website or "",
                    facebook=card.url_facebook or "",
                    instagram=card.url_instagram or "",
                )
            )

        details_order = []
        details_order.append(OrderDetail_InputDTO(
            sku=SkuRvcProductsEnum.DIGITAL_CARDS.value,
            quantity=len(digital_cards),
            totalDetailOrderValue=0.0,
            totalDetailOrderUnTaxed=0.0
        ))

        order_input = Order_InputDTO(
            nit=postulation.vat,
            orderId=str(postulation.id),
            sponsor=postulation.parent_id.vat,
            digitalCards=digital_cards,
            detailsOrder=details_order,
            buyerEmail=postulation.contact_email,
            salesmanEmail="",
            totalOrderValue=0,
            totalOrderUnTaxed=0,
            origin=OriginsEnum.ODOO.value,
            cellphone=postulation.contact_phone,
            isSeller=postulation.is_seller,
        )

        payload = order_input.model_dump()

        logging.info(
            " Postulation %d\nDigital Cards activation request: %s", postulation.id, payload
        )

        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
        response = requests.post(
            "https://gateway-odoo-prod.azurewebsites.net/gateway/activator",
            json=payload,
            headers=headers,
            timeout=10,
        )

        response_json = response.json()
        logging.info(
            "Postulation %d\nDigital Cards activation response: %s",
            postulation.id,
            response_json,
        )

        if response.status_code != 200:
            logging.error(
                "Postulation %d\nDigital Cards activation failed: %s",
                postulation.id,
                response_json,
            )
            return False

        return True
