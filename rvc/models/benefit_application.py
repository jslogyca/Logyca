# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta
from odoo.modules.module import get_module_resource
from PIL import Image, ImageDraw
from io import BytesIO
import base64
import time
import locale
import json
import re
import requests
import logging
import uuid
import textwrap
import time

_logger = logging.getLogger(__name__)

class BenefitApplication(models.Model):
    _name = 'benefit.application'
    _description = 'Postulación a beneficio'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def _default_access_token(self):
        return uuid.uuid4().hex

    state = fields.Selection([('draft', 'Draft'), 
                                    ('notified', 'Notificado'),
                                    ('confirm', 'Aceptado'),
                                    ('rejected', 'Rechazado'),
                                    ('cancel', 'Cancelado'),
                                    ('done', 'Entregado')], string='State', default='draft', readonly=True, tracking=True)
    partner_id = fields.Many2one('rvc.beneficiary', string='Empresa Beneficiaria', tracking=True, ondelete='restrict')
    parent_id = fields.Many2one('rvc.sponsor', string='Empresa Patrocinadora', tracking=True, ondelete='restrict')
    product_id = fields.Many2one('product.rvc', string='Producto', tracking=True, ondelete='restrict')
    name = fields.Char(string='Name', tracking=True)
    codes_quantity = fields.Integer('Códigos Productos', tracking=True)
    glns_codes_quantity = fields.Integer('Códigos GLN', tracking=True)
    invoice_codes_quantity = fields.Integer('Códigos Recaudo', tracking=True)
    benefit_type = fields.Selection(related='product_id.benefit_type', readonly=True, store=True, string="Beneficio", tracking=True)
    colabora_level = fields.Char(string='Nivel', tracking=True)
    end_date_colabora = fields.Date(string='Fecha Fin Colabora', tracking=True)
    acceptance_date = fields.Datetime(string='Fecha/Hora Aceptación', tracking=True, readonly=True)
    notification_date = fields.Datetime(string='Fecha/Hora Notificación', tracking=True, readonly=True)
    rejection_date = fields.Datetime(string='Fecha/Hora Rechazo', tracking=True, readonly=True)
    delivery_date = fields.Datetime(string='Fecha/Hora Entrega', tracking=True, readonly=True)
    question_answered = fields.Boolean('¿Hemos respondido tu pregunta?', default=False, tracking=True)
    gln = fields.Char('Código GLN', tracking=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company, tracking=True, ondelete='restrict')
    contact_name = fields.Char('Nombre Contacto', related='partner_id.contact_name', tracking=True)
    contact_phone = fields.Char('Teléfono Contacto', related='partner_id.contact_phone', tracking=True)
    contact_email = fields.Char('Email Contacto', related='partner_id.contact_email', tracking=True)
    contact_position = fields.Char('Cargo Contacto', related='partner_id.contact_position', tracking=True)
    vat = fields.Char('Número Documento', related='partner_id.vat', store=True, tracking=True)
    access_token = fields.Char('Token', default=_default_access_token, help="Token de acceso para aceptar beneficio desde el correo")
    send_kit_with_no_benefit = fields.Boolean('Enviar kit sin activar beneficio', help="En el caso en que el beneficio haya sido activado manualmente, esta opción \
        cuando está checkeada permite enviar el kit de bienvenida sin activar el beneficio RVC.")
    reminder_count = fields.Integer('Recordatorios', tracking=True)
    codes_count = fields.Integer(string='Contador Códigos', compute="_compute_codes_count")
    message_ids = fields.One2many(groups="rvc.group_rvc_manager")
    activity_ids = fields.One2many(groups="rvc.group_rvc_manager")
    offered_service_id = fields.Many2one('rvc.digital.card.offered.service',
        string='Servicio Ofrecido', help="Servicio que ofrece la empresa")
    partner_address = fields.Char('Dirección Empresa')
    digital_card_ids = fields.One2many('rvc.digital.card', 'postulation_id', string='Tarjetas Digitales')
    crecemype_question = fields.Text('Pregunta', help="Pregunta realizada por la empresa beneficiaria de LOGYCA / CRECEMYPE")
    crecemype_theme_id = fields.Many2one('rvc.crecemype.theme', string='Temática', tracking=True)
    # GS1 audit fields
    whatsapp_number_trail = fields.Char('Número WhatsApp', help="Número de WhatsApp que creó la postulación")
    #technical fields
    benefit_name = fields.Selection(string="Nombre Beneficio", related='product_id.benefit_type', store=True, help="Technical field used for easy quering")
    origin = fields.Selection(
        [
            ('odoo', 'Odoo'),
            ('tienda', 'Tienda Virtual'),
            ('chatbot', 'ChatBot RVC'),
            ('plataforma_rvc', 'Plataforma RVC'),
            ('api_marketplaces', 'API Marketplaces')
        ],
        string="Origen",
        tracking=True,
        default='odoo',
        readonly=True,
        help=(
            "Este campo permite diferenciar las postulaciones RVC que provienen "
            "de Odoo, Tienda Virtual, ChatBot, Plataforma RVC, API Marketplaces, etc."
        )
    )
    is_seller = fields.Boolean('Seller', default=False, tracking=True, help="La empresa vende en el marketplace del éxito?")
    referred_by = fields.Char('Referida por', tracking=True, help="¿Cómo se enteró del beneficio RVC?")
    email_employee = fields.Char('Email Colaborador')
    name_employee = fields.Char('Nombre de quién consulta')
    email_company = fields.Char('Email de quién consulta')
    product_benefit = fields.Char('Producto que maneja')
    canal = fields.Selection([('advice', 'Advice'),
                                ('email', 'Email'),], string='Canal', default='email')
    employee_id = fields.Many2one('res.partner', string='Colaborador', tracking=True, ondelete='restrict')
    date_done_cons = fields.Date(string='Date Solución', default=fields.Date.context_today)
    renewal = fields.Boolean('Renewal', default=False)
    email_colabora = fields.Char('Email Colabora', tracking=True)
    send_activated = fields.Boolean('Enviado a Activar', default=False)

    def name_get(self):
        return [(product.id, '%s - %s' % (product.partner_id.partner_id.name, product.product_id.name)) for product in self]

    @api.depends('codes_quantity', 'glns_codes_quantity', 'invoice_codes_quantity')
    def _compute_codes_count(self):
        for record in self:
            record.codes_count = record.codes_quantity + record.glns_codes_quantity + record.invoice_codes_quantity

    @api.onchange('colabora_level')
    def _onchange_colabora_level(self):
        if self.colabora_level:
            if self.colabora_level.isdigit():
                if not (1 <= int(self.colabora_level) <= 10):
                    raise UserError(_("El nivel de Colabora debe estar entre 1 y 10."))
            else:
                raise UserError(_("El nivel de Colabora debe ser un número entero entre 1 y 10."))

    def unlink(self):
        for benefit_application in self:
            if benefit_application.state not in ('draft', 'cancel'):
                raise ValidationError(_('¡Oops! No puede eliminar una postulación que no esté en estado borrador o cancelada.'))
        return super(BenefitApplication, self).unlink()

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_confirm(self):
        for benefit_application in self:
            if benefit_application.state in ('draft','notified'):
                view_id = self.env.ref('rvc.rvc_template_email_confirm_wizard_form').id,
                return {
                    'name':_("Enviar Aceptación"),
                    'view_mode': 'form',
                    'view_id': view_id,
                    'view_type': 'form',
                    'res_model': 'rvc.template.email.wizard',
                    'type': 'ir.actions.act_window',
                    'nodestroy': True,
                    'target': 'new',
                    'domain': '[]'
                }

    def action_new_credentials(self):
        for benefit_application in self:
            if benefit_application.state in ('done'):
                view_id = self.env.ref('rvc.rvc_template_assignate_credentials_wizard_form').id,
                return {
                    'name':_("Re-Asignar Credenciales"),
                    'view_mode': 'form',
                    'view_id': view_id,
                    'view_type': 'form',
                    'res_model': 'rvc.template.email.wizard',
                    'type': 'ir.actions.act_window',
                    'nodestroy': True,
                    'target': 'new',
                    'domain': '[]'
                }

    def action_done(self):
        if self.state in ('confirm'):
            # si son codigos de productos validamos que no hayan productos comprados disponibles
            if self.product_id.benefit_type == 'codigos' and self.codes_quantity > 0:
                #requiere activar beneficio con el envío del kit?
                if self.send_kit_with_no_benefit == False:
                    self._validate_bought_products()

            view_id = self.env.ref('rvc.rvc_template_email_done_wizard_form').id
            result ={'name':_("Enviar Kit de Bienvenida"),'view_mode': 'form',
                                'view_id': view_id, 'view_type': 'form', 'res_model': 'rvc.template.email.wizard',
                                'type': 'ir.actions.act_window','nodestroy': True,'target': 'new'}

            # si son codigos de productos validamos que no hayan productos comprados disponibles
            if (self.product_id.benefit_type == 'codigos' and
                (self.codes_quantity > 0 or
                 self.invoice_codes_quantity > 0 or
                 self.glns_codes_quantity > 0)):

                #requiere activar beneficio con el envío del kit?
                if self.send_kit_with_no_benefit is False:
                    if self._validate_bought_products():
                        return result
            return result

    def action_forward_done(self):
        view_id = self.env.ref('rvc.rvc_template_email_re_done_wizard_form').id,
        return {
            'name':_("Enviar Kit de Bienvenida"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'rvc.template.email.wizard',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]'
        }

    def action_rejected(self):
        for benefit_application in self:
            benefit_application.write({'state': 'rejected', 'rejection_date': datetime.now()})
            benefit_application.message_post(body=_('La postulación se marcó <b>manualmente</b> como rechazada'))

    def action_reactivate(self):
        for benefit_application in self:
            benefit_application.write({'state': 'draft'})

    def action_re_done(self):
        self.write({'state': 'confirm', 'acceptance_date': datetime.now()})

    def action_notified(self):
        for benefit_application in self:
            #Antes de notificar al beneficiario validamos si beneficio es codigos
            # y si cantidad de codigos es mayor a cero
            # y si no tiene productos comprados disponibles
            if self.product_id.benefit_type == 'codigos' and self._validate_qty_codes() and self._validate_bought_products():
                if benefit_application.state in ('draft', 'notified'):
                    view_id = self.env.ref('rvc.rvc_template_email_wizard_form').id
                    self.write({'state': 'notified', 'notification_date': datetime.now()})
                    return {
                        'name':_("Are you sure?"),
                        'view_mode': 'form',
                        'view_id': view_id,
                        'view_type': 'form',
                        'res_model': 'rvc.template.email.wizard',
                        'type': 'ir.actions.act_window',
                        'nodestroy': True,
                        'target': 'new',
                        'domain': '[]'
                    }
            #Antes de notificar al beneficiario validamos si el beneficio es colabora
            # y si el nivel de colabora está entre 1 y 10
            elif self.product_id.benefit_type == 'colabora' and self._validate_colabora_level():
                if benefit_application.state in ('draft', 'notified'):
                    view_id = self.env.ref('rvc.rvc_template_email_wizard_form').id
                    self.write({'state': 'notified', 'notification_date': datetime.now()})
                    return {
                        'name':_("Are you sure?"),
                        'view_mode': 'form',
                        'view_id': view_id,
                        'view_type': 'form',
                        'res_model': 'rvc.template.email.wizard',
                        'type': 'ir.actions.act_window',
                        'nodestroy': True,
                        'target': 'new',
                        'domain': '[]'
                    }
            elif self.product_id.benefit_type == 'analitica':
                raise ValidationError(_('Oops! Muy pronto podrás notificar el beneficio LOGYCA/ANALÍTICA.\n\n'\
                    'Por el momento solo puedes notificar DERECHOS DE IDENTIFICACIÓN y LOGYCA/COLABORA.'))
            elif not self._validate_qty_codes():
                logging.warning("===> _validate_qty_codes no pasó la validación")

    @api.model
    def create(self, vals):
        if 'partner_id' in vals and 'name' not in vals:
            beneficiary = self.env['rvc.beneficiary'].browse(vals.get('partner_id'))
            vals['name'] = beneficiary.partner_id.vat + '-' + beneficiary.partner_id.name

            if 'product_id' in vals:
                product_id = self.env['product.rvc'].browse(int(vals['product_id']))

                #este método es generico y permite saber si es apto por tamaño de empresa
                self._validate_company_size()

                #validar si producto rvc es codigos
                if product_id.code == '01':

                    # validar si está desvinculada
                    self._validate_unlinked_partner(beneficiary.partner_id)

                    # validar si es miembro o cliente
                    self._validate_member_or_client(beneficiary.partner_id)

                #validar si producto rvc es colabora
                # if product_id.code == '02':
                #     # validar si ya tiene colabora activo
                #     self._validate_has_colabora(beneficiary.partner_id.vat)

        return super(BenefitApplication, self).create(vals)

    def write(self, vals):
        res = super(BenefitApplication, self).write(vals)
        self._validate_gln_only_numbers()

        # comentado por salida a producción con proyecto 5Minutos
        # self._validate_gln()

        return res

    @api.constrains('gln')
    def _validate_gln_only_numbers(self):
        if self.gln and not re.match(r'^[0-9]+$', str(self.gln)):
            raise ValidationError(_('Código GLN "%s" es inválido.\n\nLos códigos GLN solo están compuestos de números.' % str(self.gln)))
        return True
    
    def _validate_member_or_client(self, partner_id):
        # Validar que el tipo de vinculación de la empresa beneficiaria no sea miembro, ni cliente CE
        if partner_id.x_type_vinculation:
            for vinculation in partner_id.x_type_vinculation:
                if vinculation.code in ('01', '02'):
                    validation = '%s no aplica para el beneficio. Es miembro o cliente CE' %\
                            (partner_id.vat + '-' + str(partner_id.name.strip()))
                    raise ValidationError(str(validation))
        return True

    def _validate_unlinked_partner(self, partner_id):
        """
        Valida si la empresa está desvinculada en el CRM de Odoo.

        Args:
            partner_id: Partner a validar

        Returns:
            bool: True si la validación es exitosa

        Raises:
            ValidationError: Si la empresa está desvinculada
        """
        # Validar entrada
        if not partner_id or not partner_id.x_type_vinculation:
            return True

        # Código para "No tiene vinculación"
        NO_VINCULATION_CODE = '12'

        # Verificar si tiene vinculación válida
        has_valid_vinculation = any(
            vinculation.code != NO_VINCULATION_CODE
            for vinculation in partner_id.x_type_vinculation
        )

        # Si no tiene vinculación válida Y tiene datos de desvinculación
        if (not has_valid_vinculation and
            partner_id.x_reason_desvinculation and
            partner_id.x_date_decoupling):

            company_identifier = f"{partner_id.vat}-{partner_id.name.strip()}"
            error_message = (
                f"{company_identifier} no aplica para el beneficio. "
                "Es una empresa DESVINCULADA."
            )
            raise ValidationError(error_message)

        return True

    def _get_employe(self, email):
        employee_id = self.env['res.partner'].search([('email', '=', email)], order="id asc", limit=1)
        if employee_id:
            self.write({'employee_id': employee_id.id})
        return True

    def _validate_gln(self):
        available_gln_codes = "No codes"
        gln_from_user_found = False
        qty_codes_found = 0

        if self.partner_id and (self.product_id.benefit_type == 'codigos' or \
            self.product_id.benefit_type == 'colabora' or \
            self.product_id.benefit_type == 'tarjeta_digital'):
            
            if self.get_odoo_url() == 'https://logyca.odoo.com':
                url = "https://app-asignacioncodigoslogyca-prod-v1.azurewebsites.net/codes/EmpresaGln/"
            else:
                # url = "https://app-asc-dev.azurewebsites.net/codes/EmpresaGln/"
                url = "https://app-asignacioncodigoslogyca-prod-v1.azurewebsites.net/codes/EmpresaGln/"

            payload = {'nit': str(self.vat)}

            response = requests.get(url, data=json.dumps(payload))
            logging.info(f"_Validate_gln() response: {response}")

            if response.status_code == 200:
                result = response.json()
                response.close()

                if len(result) > 0:
                    available_gln_codes = ""
                    qty_codes_found = len(result)

                for gln in result:
                    available_gln_codes = available_gln_codes + "\n" + str(gln.get('id'))

                    #caso 1: usuario ingresa un gln
                    if self.gln:
                        #caso 2: usuario ingresa gln y si está registrado.
                        if str(gln.get('id')) == self.gln:
                            gln_from_user_found = True
                            break
                    #caso 5: usuario no ingresa un gln
                    else:
                        # caso 6 y 7: usuario no ingresa gln pero se encontró que hay uno (caso 6) o varios registrados (caso 7).
                        if len(result) >= 1:
                            self.gln = result[0].get('id')
                            return True
            else:
                raise ValidationError(\
                    _('No se ha podido validar el Código GLN de la empresa seleccionada.\
                       Inténtelo nuevamente o comuníquese con soporte. Error: %s' % str(response)))

            #caso 3: usuario ingresa gln pero es incorrecto y se encuentra uno válido.
            if self.gln and gln_from_user_found == False and available_gln_codes != "No codes" and qty_codes_found == 1:
                raise ValidationError(\
                    _('El código GLN ingresado es incorrecto, sin embargo encontramos uno registrado:\n\
                        %s \n\nPor favor copie y pegue éste.' % str(available_gln_codes)))
            #caso 4: usuario ingresa gln incorrecto pero hay varios válidos registrados.
            elif self.gln and gln_from_user_found == False and available_gln_codes != "No codes":
                raise ValidationError(\
                    _('El código GLN "%s" no es válido, sin embargo encontramos los siguientes %s códigos registrados: \n\
                        %s \n\nPor favor copie y pegue alguno.' % (self.gln, str(qty_codes_found), str(available_gln_codes))))
            #caso 8: no tiene gln registrado. Registrando uno para la empresa seleccionada.
            elif not self.gln and gln_from_user_found == False and available_gln_codes == "No codes":
                logging.info(" ==> Se asignará GLN con el beneficio <===")
                return False

            #caso 9: usuario ingresa GLN pero es incorrecto y no tiene GLN's.
            elif self.gln and gln_from_user_found == False and available_gln_codes == "No codes":
                partner_id = False

                #es un contacto
                if self.partner_id.partner_id.is_company == False or self.partner_id.partner_id.parent_id:
                    partner_id = self.partner_id.partner_id.parent_id
                else:
                    partner_id = self.partner_id.partner_id
                tmp_code = str(self.gln)

                # raise ValidationError(\
                #     _('El Código GLN "%s" es inválido. La empresa "%s" no tiene código(s) GLN registrados.'\
                #     '\n\nPor favor deje el campo Código GLN vacío, le asignaremos uno en la entrega del beneficio.' % (tmp_code, str(partner_id.name))))

    def _validate_bought_products(self):
        """
        Valida si la empresa ha consumido más del 80% de sus códigos NPV comprados.
        Si es así, lanza un ValidationError.
        """
        # Obtener token de autenticación
        token = self.get_token_sso()
        if not token:
            raise ValidationError(
                _(
                    'No se pudo obtener el token de autenticación para validar códigos comprados. '
                    'Inténtelo nuevamente o comuníquese con soporte.'
                )
            )

        # Determinar URL según el entorno
        if self.get_odoo_url() == 'https://logyca.odoo.com':
            url = (
                "https://app-msprefixcodesservice-prod.azurewebsites.net/api/"
                "code_reservation_service/get_code_summary_by_enterprise/"
                f"{str(self.vat)}"
            )
        else:
            url = (
                "https://app-msprefixcodesservice-dev.azurewebsites.net/api/"
                "code_reservation_service/get_code_summary_by_enterprise/"
                f"{str(self.vat)}"
            )

        # Configurar headers con el token
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }

        try:
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                result = response.json()
                response.close()

                # Verificar si la respuesta tiene errores
                if result.get('dataError', True) or \
                result.get('apiException', {}).get('isError', True):
                    error_message = result.get('apiException', {}).get(
                        'message', 'Error desconocido'
                    )
                    raise ValidationError(
                        _(
                            f"Error al obtener información de códigos: "
                            f"{error_message}"
                        )
                    )

                # Obtener datos del objeto resultado
                result_object = result.get('resultObject', {})
                total_npv_codes = result_object.get('total_npv_codes_purchased', 0)
                available_npv_codes = result_object.get('total_available_npv_codes_purchased', 0)

                # Validar que tenemos datos válidos
                if total_npv_codes == 0:
                    # Si no tiene códigos comprados, permitir el beneficio
                    return True

                # Aplicar reglas de validación según el total de códigos comprados
                vat_name = f"{self.partner_id.partner_id.vat}-{self.partner_id.partner_id.name}"

                if total_npv_codes > 50:
                    # Para empresas con más de 50 códigos totales:
                    # aplicar regla del 80% (más del 20% disponible)
                    percentage_available = (available_npv_codes / total_npv_codes) * 100

                    if percentage_available > 20:
                        msg = (
                            f"¡Lo sentimos! La empresa {vat_name} tiene "
                            f"{available_npv_codes} código(s) comprados disponibles "
                            f"({percentage_available:.1f}% del total de "
                            f"{total_npv_codes} códigos). "
                            "Debe consumir al menos el 80% de sus códigos antes de solicitar más."
                        )
                        raise ValidationError(_(msg))
                else:
                    # Para empresas con 50 códigos totales o menos:
                    # validar que tenga menos de 10 códigos disponibles
                    if available_npv_codes >= 10:
                        msg = (
                            f"¡Lo sentimos! La empresa {vat_name} tiene "
                            f"{available_npv_codes} código(s) comprados disponibles "
                            f"de un total de {total_npv_codes} códigos. "
                            f"Debe tener menos de 10 códigos disponibles para solicitar más."
                        )
                        raise ValidationError(_(msg))

                return True

            elif response.status_code == 500:
                # Verificar si es un error 500 con mensaje específico de NIT no encontrado
                try:
                    result = response.json()
                    result_message = result.get('resultMessage', '')

                    # Si el NIT no fue encontrado, permitir el beneficio
                    if result_message == "El NIT no fue encontrado":
                        response.close()
                        return True
                    else:
                        # Si es otro tipo de error 500, lanzar excepción
                        response.close()
                        raise ValidationError(
                            _(
                                "Error interno del servidor al validar códigos comprados. "
                                "Inténtelo nuevamente o comuníquese con soporte. "
                                f"Error: {response.status_code} - {result_message}"
                            )
                        )
                except (ValueError, KeyError) as exc:
                    # Si no se puede parsear el JSON o no tiene la estructura esperada
                    response.close()
                    raise ValidationError(
                        _(
                            "Error interno del servidor al validar códigos comprados. "
                            "Inténtelo nuevamente o comuníquese con soporte. "
                            f"Error: {response.status_code}"
                        )
                    ) from exc
            else:
                raise ValidationError(
                    _(
                        "No se pudo validar si la empresa seleccionada tiene "
                        "códigos comprados disponibles. "
                        "Inténtelo nuevamente o comuníquese con soporte. "
                        f"Error: {response.status_code}"
                    )
                )

        except requests.exceptions.RequestException as e:
            raise ValidationError(
                _(
                    'Error de conexión al validar códigos comprados. '
                    'Inténtelo nuevamente o comuníquese con soporte. '
                    f'Error: {str(e)}'
                )
            ) from e

    def _validate_qty_codes(self):
        for rec in self:
            if rec.codes_quantity == 0 and rec.glns_codes_quantity == 0 and rec.invoice_codes_quantity == 0 and self.product_id.benefit_type == 'codigos':
                raise ValidationError(\
                    _('Por favor indique la Cantidad de Códigos que se entregará a la empresa beneficiaria.\n\nEmpresa: %s' % (str(self.partner_id.partner_id.name))))
        return True

    def _validate_colabora_level(self):
        for rec in self:
            if not rec.colabora_level  and self.product_id.benefit_type == 'colabora':
                raise ValidationError(\
                    _('Por favor indique el Nivel de LOGYCA/COLABORA que desea activar para la empresa beneficiaria.\n\nEmpresa: %s' % (str(self.partner_id.partner_id.name))))
        return True

    def _validate_company_size(self):
        for rec in self:

            #validar que para D.I sean mipymes
            if rec.partner_id.partner_id.x_company_size and rec.partner_id.partner_id.x_company_size == '4' and self.product_id.benefit_type == 'codigos':
                raise ValidationError(\
                    _('¡Error de Validación! La empresa es grande.\n\nEmpresa: %s' % (str(self.partner_id.partner_id.name))))

            #validar que para colabora sean mypes
            if rec.partner_id.partner_id.x_company_size and rec.partner_id.partner_id.x_company_size in ['5','6'] and self.product_id.benefit_type == 'colabora':
                raise ValidationError(\
                    _('¡Error de Validación! La empresa NO es micro o pequeña.\n\nEmpresa: %s' % (str(self.partner_id.partner_id.name))))
        return True

    def assignate_gln_code(self, qty=None):
        #creando código
        if self.get_odoo_url() == 'https://logyca.odoo.com':
            url_assignate = "https://app-asignacioncodigoslogyca-prod-v1.azurewebsites.net/codes/assignate/"
        else:
            url_assignate = "https://app-asc-dev.azurewebsites.net/codes/assignate/"

        body_assignate = json.dumps({
            "AgreementName":"",
            "IdAgreement":"1",
            "Request": [{
                "Quantity": qty or 1,
                "Nit": self.vat,
                "PreferIndicatedPrefix": False,
                "BusinessName": self.partner_id.partner_id.name,
                "Schema": 2,
                "ScalePrefixes": False,
                "Type": 55603,
                "PrefixType": "",
                "VariedFixedUse": False}],
                "UserName": "Admin"})
        headers_assignate = {'Content-Type': 'application/json'}
        
        #Making http post request
        response_assignate = requests.post(url_assignate, headers=headers_assignate, data=body_assignate, verify=True)

        if response_assignate.status_code == 200:
            #obteniendo el prefijo del código
            json_res = response_assignate.json()
            txt_response = json_res.get('MensajeUI')[0]
            prefix = ", ".join(item.split(": ")[1] for item in txt_response)

            response_assignate.close()
            
            #marcando código
            if self.get_odoo_url() == 'https://logyca.odoo.com':
                url_mark = "https://app-asignacioncodigoslogyca-prod-v1.azurewebsites.net/codes/mark/"
            else:
                url_mark = "https://app-asc-dev.azurewebsites.net/codes/mark/"

            body_mark = json.dumps({
                "Nit": self.vat,
                "TipoProducto": 1,
                "Username": "RVC",
                "Esquemas": [
                    2,
                    3,
                    6
                ],
                "Codigos": [
                    {
                        "Descripcion": "Gln Empresa %s" % str(self.partner_id.partner_id.name),
                        "TipoProducto": 4
                    }
                ]
            })
            headers_mark = {'Content-Type': 'application/json'}
            response_mark = requests.post(url_mark, headers=headers_mark, data=body_mark, verify=True)

            if response_mark.status_code == 200:
                response_mark.close()
                result = response_mark.json()
                logging.info("====> response al marcar GLN =>\n" + str(result))

                #si es un solo GLN entonces ...
                if not qty or self.glns_codes_quantity == 1:
                    self.write({'gln': str(result.get('IdCodigos')[0].get('Codigo'))})
                    self.message_post(body=_(f'Código(s) GLN fue creado y entregado con el beneficio. Prefijo: {str(prefix)}'))
                    logging.info(\
                        "Código GLN '%s' creado y marcado para la empresa %s"\
                            % (result.get('IdCodigos')[0].get('Codigo'), str(self.partner_id.partner_id.name)))

                #de lo contrario, son varios gln
                else:
                    self.message_post(body=_(f'Los {int(self.glns_codes_quantity)} Códigos GLN fueron creados y entregados con el beneficio. Prefijo(s): {str(prefix)}'))
        else:
            self.message_post(body=_('No se pudo asignar al beneficiario el/los Código(s) GLN. El servidor respondió %s' % str(response_assignate)))

    def assign_identification_codes(self):

        if self.get_odoo_url() == 'https://logyca.odoo.com':
            url_assignate = "https://app-asignacioncodigoslogyca-prod-v1.azurewebsites.net/codes/assignate/"
        else:
            url_assignate = "https://app-asc-dev.azurewebsites.net/codes/assignate/"

        body_assignate = json.dumps({
            "AgreementName":"",
            "IdAgreement":"",
            "Request": [{
                "Quantity": int(self.codes_quantity),
                "Nit": self.vat,
                "PreferIndicatedPrefix": False,
                "BusinessName": self.partner_id.partner_id.name,
                "Schema": 2,
                "ScalePrefixes": False,
                "Type": 55600,
                "PrefixType": "",
                "VariedFixedUse": False}],
                "UserName": "Admin"})
        headers_assignate = {'Content-Type': 'application/json'}

        #Making http post request
        response_assignate = requests.post(url_assignate, headers=headers_assignate, data=body_assignate, verify=True)

        logging.info("====> response_assignate_codes_to_beneficiary =>" + str(response_assignate))

        if response_assignate.status_code == 200:
            #obteniendo el prefijo del código
            json_res = response_assignate.json()
            txt_response = json_res.get('MensajeUI')[0]
            prefix = ", ".join(item.split(": ")[1] for item in txt_response)

            response_assignate.close()
            self.message_post(body=_(f'Los {str(int(self.codes_quantity))} Códigos de Identificación fueron entregados al beneficiario. Prefijo(s): {str(prefix)}'))
            return True
        else:
            #TODO: logging
            self.message_post(body=_('Los Códigos de Identificación no pudieron ser entregados al beneficiario. <strong>Error:</strong> %s' % str(response_assignate)))
            return False

    def assign_invoice_codes(self):
        """
            Función que asigna códigos de recaudo
            TODO: esta función es la misma que la que se usa para asignar codigos de identificación y GLN's. Intentar reusar código.
                  lo único que cambia es la variable type 55800=recaudo, 55600=codigos productos, 55603= gln's
        """
        if self.get_odoo_url() == 'https://logyca.odoo.com':
            url_assignate = "https://app-asignacioncodigoslogyca-prod-v1.azurewebsites.net/codes/assignate/"
        else:
            url_assignate = "https://app-asc-dev.azurewebsites.net/codes/assignate/"

        body_assignate = json.dumps({
            "AgreementName":"",
            "IdAgreement":"",
            "Request": [{
                "Quantity": int(self.invoice_codes_quantity),
                "Nit": self.vat,
                "PreferIndicatedPrefix": False,
                "BusinessName": self.partner_id.partner_id.name,
                "Schema": 2,
                "ScalePrefixes": False,
                "Type": 55800,
                "PrefixType": "",
                "VariedFixedUse": False}],
                "UserName": "Admin"})
        headers_assignate = {'Content-Type': 'application/json'}

        #Making http post request
        response_assignate = requests.post(url_assignate, headers=headers_assignate, data=body_assignate, verify=True)

        logging.info("====> response_assignate_invoice_codes =>" + str(response_assignate))

        if response_assignate.status_code == 200:
            #obteniendo el prefijo del código
            json_res = response_assignate.json()
            txt_response = json_res.get('MensajeUI')[0]
            prefix = ", ".join(item.split(": ")[1] for item in txt_response)

            #cerrando request
            response_assignate.close()
            self.message_post(body=_(f'Los {str(int(self.invoice_codes_quantity))} Códigos de Recaudo fueron entregados al beneficiario. Prefijo(s): {str(prefix)}'))
            return True
        else:
            #TODO: logging
            self.message_post(body=_('Los Códigos de Recaudo no pudieron ser entregados al beneficiario. <strong>Error:</strong> %s' % str(response_assignate)))
            return False

    def get_token_colabora_api(self):
        
        if self.get_odoo_url() == 'https://logyca.odoo.com':
            url_get_token = "https://app-loginrocp-prod.azurewebsites.net/api/Login"
        else:
            url_get_token = "https://app-loginrocp-prod.azurewebsites.net/api/Login"
            # url_get_token = "https://app-loginrocp-dev.azurewebsites.net/api/Login"   

        body_get_token = json.dumps({
            "email": "odoorvc@yopmail.com",
            "password": "Logyca09062829"
        })

        headers_get_token = {'Content-Type': 'application/json'}
        response_get_token = requests.post(url_get_token, headers=headers_get_token, data=body_get_token, verify=True)

        if response_get_token.status_code == 200:
            result = response_get_token.json()
            response_get_token.close()
            token = str(result.get('resultToken').get('token'))
            return token

        return False

    def get_token_sso(self):
        """ token auth in SSO

        Returns:
            [str]: token for api access or False
        """
        
        if self.get_odoo_url() == 'https://logyca.odoo.com':
            url_get_token = "https://app-loginrocp-prod.azurewebsites.net/api/Login"
        else:
            url_get_token = "https://app-loginrocp-dev.azurewebsites.net/api/Login"

        body_get_token = json.dumps({
            "email": "odoorvc@yopmail.com",
            "password": "Logyca09062829"
        })

        headers_get_token = {'Content-Type': 'application/json', 'Connection': 'keep-alive'}

        max_retries = 3
        retry_delay = 2

        for retry in range(max_retries):
            try:
                response_get_token = requests.post(url_get_token, headers=headers_get_token, data=body_get_token, verify=False)
                if response_get_token.status_code == 200:
                    result = response_get_token.json()
                    response_get_token.close()
                    token = str(result.get('resultToken').get('token'))
                    return token
            except requests.exceptions.RequestException:
                pass

            time.sleep(retry_delay)

        return False

    def assign_credentials_gs1codes(self, re_assign=False, re_assign_email=None):
        bearer_token = self.get_token_sso()
        today_date = datetime.now()

        if bearer_token or bearer_token[0]:
            today_one_year_later = today_date + relativedelta(years=1)

            if self.get_odoo_url() == 'https://logyca.odoo.com':
                url_assignate= "https://app-msadenterprise-prod.azurewebsites.net/api/Company/AddCompanyEcommerce"
            else:
                # url_assignate= "https://app-colaborags1api-dev.azurewebsites.net/api/Company/AddCompanyEcommerce"
                url_assignate= "https://app-msadenterprise-prod.azurewebsites.net/api/Company/AddCompanyEcommerce"

            #validando el nombre de contacto para asignar credenciales
            # si no tiene contact_name le ponemos el nombre de la empresa
            credentials_contact_name = ""
            if self.contact_name:
                credentials_contact_name = self.contact_name
            elif self.partner_id.partner_id.name:
                credentials_contact_name = self.partner_id.partner_id.name
            elif self.partner_id.partner_id.x_first_name and self.partner_id.partner_id.x_first_lastname:
                credentials_contact_name = self.partner_id.partner_id.x_first_name + " " + self.partner_id.partner_id.x_first_lastname

            # si viene de reasignar credenciales utiliza el correo nuevo ingresado y si no usa el
            # que tiene el contacto del beneficiario
            contact_email = re_assign_email if re_assign_email is not None else self.contact_email

            colabora_initial_date = today_date.strftime('%Y-%m-%d')

            body_assignate = json.dumps({
                    "Nit": self.vat,
                    "Name": credentials_contact_name,
                    "UserMail": contact_email,
                    "InitialDate": colabora_initial_date,
                    "EndDate": today_one_year_later.strftime('%Y-%m-%d'),
                    "level": 1,
                    "TypeService": 1,
                    "NumberOverConsumption": 0,
                    "IsOverconsumption": False
                })
            headers_assignate = {'Content-Type': 'application/json', 'Authorization': 'Bearer %s' % bearer_token}

            #Making http post request
            response_assignate = requests.post(url_assignate,
                                               headers=headers_assignate,
                                               data=body_assignate,
                                               verify=True,
                                               timeout=10)

            logging.info("====> response_assignate_credentials => %s", str(response_assignate))

            if response_assignate.status_code == 200:
                #TODO: logging
                result = response_assignate.json()
                response_assignate.close()

                #error al crear credenciales
                if result.get('dataError') is True or result.get('apiException').get('status') != 200:
                    #TODO: logging
                    error_message = result.get('apiException').get('message')
                    if not error_message:
                        error_message = result.get('resultMessage')
                    self.message_post(body=_(f'No pudieron asignarse las credenciales para GS1-ASC.\n<strong>Error:</strong> {str(error_message)}'))
                    return False

                self.message_post(body=_('Las credenciales para acceder a la administración de códigos fueron entregadas con el beneficio.'))
                return True
            else:
                vals = {
                    'method': 'gs1_assign_credentials',
                    'send_date': today_date.strftime('%Y-%m-%d'),
                    'send_json': body_assignate,
                    'x_return': str(response_assignate.text),
                    'cant_attempts': 1,
                }
                create_log = self.env['logyca.api_gateway'].create(vals)
                if create_log:
                    log = "Se creó un registro en el log de errores."
                else:
                    log = "No se pudo crear un registro de log de errores."

                #TODO: logging
                logging.exception("====> assign_credentials_gs1codes => %s", str(response_assignate))

                self.message_post(body=f'No pudieron asignarse las credenciales. <strong>Error:</strong> {str(response_assignate)}. {str(log)}')
                return False
        else:
            self.message_post(body=_("No pudo obtenerse el token para realizar la asignación de credenciales en www.gs1coidentificacion.org."\
                                     "Inténtelo nuevamente o comuníquese con soporte."))
            return False

    def assign_credentials_colabora(self, re_assign=False, re_assign_email=None):
        bearer_token = self.get_token_colabora_api()

        if bearer_token or bearer_token[0]:
            today_date = datetime.now()
            today_one_year_later = today_date + relativedelta(years=1)

            if self.get_odoo_url() == 'https://logyca.odoo.com':
                url_assignate= "https://app-mstransaction-prod.azurewebsites.net/api/Company/AddCompanyEcommerce"
            else:
                # url_assignate= "https://logycacolaboratestapi.azurewebsites.net/api/Company/AddCompanyEcommerce"
                # url_assignate= "https://app-mstransaction-release.azurewebsites.net/api/Company/AddCompanyEcommerce"
                url_assignate= "https://app-mstransaction-prod.azurewebsites.net/api/Company/AddCompanyEcommerce"

            
            #validando el nombre de contacto para asignar credenciales
            # si no tiene contact_name le ponemos el nombre de la empresa
            print('%%%%%%', url_assignate)
            credentials_contact_name = ""
            if self.contact_name:
                credentials_contact_name = self.contact_name
            elif self.partner_id.partner_id.name:
                credentials_contact_name = self.partner_id.partner_id.name
            elif self.partner_id.partner_id.x_first_name and self.partner_id.partner_id.x_first_lastname:
                credentials_contact_name = self.partner_id.partner_id.x_first_name + " " + self.partner_id.partner_id.x_first_lastname
            
            # si viene de reasignar credenciales utiliza el correo nuevo ingresado y si no usa el 
            # que tiene el contacto del beneficiario
            contact_email = re_assign_email if re_assign_email != None else self.contact_email

            year = int(self.end_date_colabora.strftime("%Y"))
            InitialDate = self.end_date_colabora.replace(year=year-1)
            if self.email_colabora:
                contact_email = self.email_colabora
            else:
                contact_email = self.contact_email
            body_assignate = json.dumps({
                    "TypeService": 2,
                    "Name": credentials_contact_name,
                    "Nit": self.vat,
                    "GLN": self.gln,
                    "InitialDate": str(InitialDate),
                    "EndDate": str(self.end_date_colabora),
                    "UserMail": contact_email,
                    "level": self.colabora_level,
                    "IsOverconsumption": False,
                    "NumberOverConsumption": 0,
                    "IsSponsored":  True,
                    "IsTextil": False
                })               
            headers_assignate = {'Content-Type': 'application/json', 'Authorization': 'Bearer %s' % bearer_token}
            print('%%%%%%', body_assignate)
            #Making http post request
            response_assignate = requests.post(url_assignate, headers=headers_assignate, data=body_assignate, verify=True)
            print('%%%%%%', body_assignate)
            # logging.info("====> response_assignate_credentials =>" + str(response_assignate))
            print('%%%%%% 222', response_assignate.status_code)
            if response_assignate.status_code == 200:
                #TODO: logging
                result = response_assignate.json()
                response_assignate.close()
                print('%%%%%% 3333', result)
                #error al crear credenciales
                if result.get('dataError') == True:
                    #TODO: logging
                    error_message = result.get('apiException').get('message')
                    if not error_message:
                        error_message = result.get('resultMessage')
                    self.message_post(body=_(\
                        'No pudieron asignarse las credenciales para acceder a la administración de códigos.'\
                            '\n<strong>Error:</strong> %s' % str(error_message)))
                    return False
                else:
                    self.message_post(body=_('Las credenciales para acceder a la administración de códigos fueron entregadas con el beneficio.'))
                    return True
            else:
                #TODO: logging
                # logging.exception("====> assign_credentials_gs1codes =>" + str(response_assignate))
                # logging.exception("====> assign_credentials_gs1codes =>" + str(response_assignate.text))
                self.message_post(body=_(\
                        'No pudieron asignarse las credenciales. <strong>Error:</strong> %s' % str(response_assignate)))
                return False
        else:
            self.message_post(body=_("No pudo obtenerse el token para realizar la asignación de credenciales en Colabora."\
                                     "Inténtelo nuevamente o comuníquese con soporte."))
            return False

    def assign_colabora(self):
        bearer_token = self.get_token_colabora_api()

        if bearer_token or bearer_token[0]:
            today_date = datetime.now()
            today_one_year_later = today_date + relativedelta(years=1)

            if self.get_odoo_url() == 'https://logyca.odoo.com':
                url_assignate= "https://app-mstransaction-prod.azurewebsites.net/api/Company/AddCompanyEcommerce"
            else:
                # url_assignate= "https://app-mstransaction-release.azurewebsites.net/api/Company/AddCompanyEcommerce"
                # url_assignate= "https://app-mstransaction-dev.azurewebsites.net/api/Company/AddCompanyEcommerce"
                url_assignate= "https://app-mstransaction-prod.azurewebsites.net/api/Company/AddCompanyEcommerce"

            #validando el nombre de contacto para asignar credenciales
            # si no tiene contact_name le ponemos el nombre de la empresa
            print('%%%%%%', url_assignate)
            credentials_contact_name = ""
            if self.contact_name:
                credentials_contact_name = self.contact_name
            elif self.partner_id.partner_id.name:
                credentials_contact_name = self.partner_id.partner_id.name
            elif self.partner_id.partner_id.x_first_name and self.partner_id.partner_id.x_first_lastname:
                credentials_contact_name = self.partner_id.partner_id.x_first_name + " " + self.partner_id.partner_id.x_first_lastname
            year = int(self.end_date_colabora.strftime("%Y"))
            InitialDate = self.end_date_colabora.replace(year=year-1)
            if self.email_colabora:
                contact_email = self.email_colabora
            else:
                contact_email = self.contact_email
            body_assignate = json.dumps({
                    "TypeService": 2,
                    "Name": credentials_contact_name,
                    "Nit": self.vat,
                    "GLN": self.gln,
                    "InitialDate": str(InitialDate),
                    "EndDate": str(self.end_date_colabora),
                    "UserMail": contact_email,
                    "level": self.colabora_level,
                    "IsOverconsumption": False,
                    "NumberOverConsumption": 0,
                    "IsSponsored":  True,
                    "IsTextil": False
                })
            headers_assignate = {'Content-Type': 'application/json', 'Authorization': 'Bearer %s' % bearer_token}
            #Making http post request
            response_assignate = requests.post(url_assignate, headers=headers_assignate, data=body_assignate, verify=True)
            logging.info("====> response_assignate_colabora =>" + str(response_assignate))
            print('%%%%%% 222', response_assignate.status_code)
            print('%%%%%%', body_assignate)
            if response_assignate.status_code == 200:
                #TODO: logging
                result = response_assignate.json()
                response_assignate.close()
                print('%%%%%% 333', result)
                #TODO: se requiere que la API de Colabora nos devuelva dataError=False cuando sea exitosa la asignacion de colabora
                #la condición está al revés, es decir, se espera que en el caso ideal devuelva dataError=True. 
                if result.get('dataError') == True:
                    #TODO: logging
                    error_message = result.get('apiException').get('message')
                    if not error_message:
                        error_message = result.get('resultMessage')
                    self.message_post(body=_(\
                        'No pudo activarse colabora.\n<strong>Error:</strong> %s' % str(error_message)))
                    return False

                #error al asignar colabora
                else:
                    self.message_post(body=_('Se ha <strong>activado</strong> Colabora <strong>nivel ' + str(self.colabora_level) + '</strong>'))
                    return True
            else:
                #TODO: logging
                logging.exception("====> assign_colabora =>" + str(response_assignate))
                logging.exception("====> assign_colabora =>" + str(response_assignate.text))
                self.message_post(body=_(\
                        'No pudo activarse colabora.\n<strong>Error:</strong> %s' % str(response_assignate)))
                return False
        else:
            self.message_post(body=_("No pudo obtenerse el token para realizar la activación de Colabora."\
                                     "Inténtelo nuevamente o comuníquese con soporte."))
            return False

    def today_date_spanish(self):
        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
        return datetime.now().strftime('%d de %B de %Y')

    def update_contact(self, company_id):
        type_id = self.env.ref('rvc.contact_types_rvc').id,
        self._cr.execute(''' SELECT id FROM res_partner WHERE email=%s AND is_company IS False
                                AND parent_id=(SELECT id FROM res_partner WHERE vat=%s AND is_company IS True AND active IS TRUE) ''',
                                            (company_id.contact_email, company_id.vat))
        contact_id= self._cr.fetchone()
        if contact_id and contact_id[0]:
            self._cr.execute(\
                ''' SELECT * FROM logyca_contact_types_res_partner_rel WHERE res_partner_id=%s AND logyca_contact_types_id=%s ''', (contact_id[0], type_id))
            type_contact = self._cr.fetchone()
            if not type_contact:
                self._cr.execute(''' INSERT INTO logyca_contact_types_res_partner_rel
                                        (res_partner_id, logyca_contact_types_id) SELECT %s, %s ''', (contact_id[0], type_id))
        else:
            contact_new = self.env['res.partner'].create({
                                        'name': company_id.contact_name,
                                        'street': company_id.partner_id.street,
                                        'country_id': company_id.partner_id.country_id.id,
                                        'state_id': company_id.partner_id.state_id.id,
                                        'email': company_id.contact_email,
                                        'phone': company_id.contact_phone,
                                        'vat': company_id.vat,
                                        'parent_id': company_id.partner_id.id,
                                        'x_city': company_id.partner_id.x_city.id})
            self._cr.execute(''' INSERT INTO logyca_contact_types_res_partner_rel
                                    (res_partner_id, logyca_contact_types_id) SELECT %s, %s ''', (contact_new.id, type_id))
        return True

    def update_company(self, company_id):
        self._cr.execute(''' UPDATE res_partner SET x_sponsored=%s, x_flagging_company=%s WHERE id=%s ''',
                                        (True, company_id.parent_id.partner_id.id, company_id.partner_id.partner_id.id))
        return True

    def add_vinculation_partner(self):
        for record in self:
            try:
                partner_id = record.partner_id.partner_id
                vinculation_99_anos_id = self.env['logyca.vinculation_types'].search([('name','=','99 Años')],limit=1)
                # si el partner no tiene una vinculación activa entonces lo vinculamos como 99 anios
                if partner_id.x_active_vinculation == False:
                    partner_id.x_type_vinculation = [(6,0, vinculation_99_anos_id.ids)]
                    partner_id.x_active_vinculation = True
                    partner_id.x_date_vinculation = date.today()
                    record.message_post(body=_(\
                                'Se activó la vinculación: <strong>%s</strong>' % str(vinculation_99_anos_id.name)))
                # si tiene una vinculacion activa entonces le adicionamos la 99 anios
                else:
                    # si tiene al menos un tipo de vinculacion entonces revisamos cuáles son
                    if partner_id.x_type_vinculation:
                        for vinculation in partner_id.x_type_vinculation:
                            # tiene la vinculación 'no tiene vinculacion' o tiene la '99 anos'
                            if vinculation.code in ('12', '10'):
                                #reemplazamos la vinculacion por la '99 anos' y a fecha activacion sera hoy
                                partner_id.x_type_vinculation = [(6,0, vinculation_99_anos_id.ids)]
                                partner_id.x_date_vinculation = date.today()
                                record.message_post(body=_(\
                                'Se activó la vinculación: <strong>%s</strong>' % str(vinculation_99_anos_id.name)))
                            else:
                                #agregamos la vinculacion 99 anios y ponemos fecha activacion hoy
                                partner_id.x_type_vinculation = [(4, vinculation_99_anos_id.id)]
                                partner_id.x_date_vinculation = date.today()
                                record.message_post(body=_(\
                                            'Se adicionó la vinculación: <strong>%s</strong>' % str(vinculation_99_anos_id.name)))
            except Exception as e:
                record.message_post(body=_(\
                    '<strong>¡Error!</strong> No se pudo activar la vinculación <strong>%s</strong>. Descripción: %s' % (str(vinculation_99_anos_id.name), str(e))))

    def action_reminder(self):
        """ This function allows you to notify by email if the application is non accepted."""
        postulation = self

        if postulation.reminder_count == 3:
            postulation.message_post(body=_('La postulación se marcó como rechazada dado que se notificó recordatorio '\
                    'en tres (3) oportunidades y no se aceptó el beneficio por parte de la empresa.'))
            postulation.state = 'rejected'
        else:
            self.send_reminder_benefit_expiration(postulation)

    def _cron_send_welcome_kit(self):
        """Acción planificada que activa servicios RVC para las postulaciones Aceptadas."""

        logging.warning("==> Iniciando cron de activación de servicios RVC ...")

        # Buscar postulaciones en estado 'confirm' que necesiten activación
        postulations = self.search([
            ('state', '=', 'confirm'),
            ('codes_quantity', '<=', 1000),
            ('origin', '=', 'odoo')
        ], order="id asc")

        for postulation_id in postulations:
            # Limitamos la activación para no saturar el servidor
            if counter >= 30:
                logging.warning(
                    "====> Cron alcanzó el límite de activaciones, "
                    "esperando la próxima ejecución para procesar más..."
                )
                break

            # Validar que tenga email de contacto
            if not postulation_id.partner_id.contact_email:
                postulation_id.message_post(
                    body=_(
                        '🚫 No se pudo activar el beneficio porque la empresa '
                        'no tiene email de contacto.'
                    )
                )
                counter += 1
                continue

            # Validar si tiene aún códigos disponibles (para rechazar la postulación)
            # la empresa debe haber consumido o asignado sus codigos disponibles para pedir más
            if postulation_id.product_id.benefit_type == 'codigos':
                try:
                    postulation_id._validate_bought_products()
                except ValidationError:
                    postulation_id.message_post(
                        body=_(
                            '🚫 No se pudo activar porque la empresa '
                            f'{postulation_id.partner_id.partner_id.vat}-'
                            f'{postulation_id.partner_id.partner_id.name} '
                            'tiene códigos disponibles por asignar. '
                            'La postulación se marca como rechazada.'
                        )
                    )
                    postulation_id.write({'state': 'rejected', 'rejection_date': datetime.now()})
                    counter += 1
                    continue

            # Activar servicios usando rvc.activations
            activated = False
            try:
                if postulation_id.product_id.benefit_type == 'codigos':
                    activated = self.env['rvc.activations'].activate_gs1_codes(postulation_id)
                    if activated:
                        postulation_id.message_post(body=_('✅ Se activó correctamente el beneficio de Códigos GS1.'))
                    else:
                        postulation_id.message_post(body=_('🚫 No se pudo activar el beneficio de Códigos GS1.'))

                elif postulation_id.product_id.benefit_type == 'colabora':
                    activated = self.env['rvc.activations'].activate_logyca_colabora(postulation_id)
                    if activated:
                        postulation_id.message_post(body=_('✅ Se activó correctamente el beneficio LOGYCA / COLABORA.'))
                    else:
                        postulation_id.message_post(body=_('🚫 No se pudo activar el beneficio LOGYCA / COLABORA.'))

                elif postulation_id.product_id.benefit_type == 'tarjeta_digital':
                    if postulation_id.digital_card_ids:
                        activated = self.env['rvc.activations'].activate_digital_cards(postulation_id)
                        if activated:
                            postulation_id.message_post(body=_('✅ Se activó correctamente el beneficio de Tarjetas Digitales.'))
                        else:
                            postulation_id.message_post(body=_('🚫 No se pudo activar el beneficio de Tarjetas Digitales.'))
                    else:
                        postulation_id.message_post(body=_(
                            '🚫 No se pudo activar el beneficio de Tarjetas Digitales porque no hay tarjetas configuradas.'
                        ))

                # Si se activó correctamente, cambiar estado a 'done'
                if activated:
                    postulation_id.write({'state': 'done', 'delivery_date': datetime.now()})

            except Exception as e:
                postulation_id.message_post(
                    body=_(
                        '🚫 Error inesperado al activar el beneficio {}: {}'
                    ).format(
                        postulation_id.product_id.benefit_type,
                        str(e)
                    )
                )
                logging.exception(
                    "Error en cron de activación para postulación %s: %s",
                    postulation_id.id,
                    str(e)
                )

            counter += 1

        logging.warning(
            "==> Finalizando cron de activación de servicios RVC. "
            "Procesados: %s registros",
            counter
        )

    def _cron_mark_as_rejected(self):
        logging.warning("==> Iniciando cron de marcar postulaciones como rechazadas ...")

        postulations = self.search([
            ('state', '=', 'notified'),
            ('notification_date', '<', datetime.now() - relativedelta(days=31))
        ])

        logging.warning(
            "==> Se encontraron %s postulaciones para marcar como rechazadas",
            len(postulations)
        )

        counter = 0
        for postulation_id in postulations:
            try:
                vat = postulation_id.partner_id.partner_id.vat
                name = postulation_id.partner_id.partner_id.name

                logging.info(
                    "==> Procesando postulación ID: %s - Empresa: %s-%s",
                    postulation_id.id,
                    vat,
                    name
                )

                postulation_id.write({
                    'state': 'rejected',
                    'rejection_date': datetime.now()
                })
                postulation_id.message_post(
                    body=_(
                        'La postulación se marcó como rechazada dado que pasaron más de 30 días '
                        'desde su notificación y no fue aceptado el beneficio.'
                    )
                )

                logging.info(
                    "==> Postulación ID: %s marcada como rechazada exitosamente",
                    postulation_id.id
                )
                counter += 1

            except Exception as e:
                logging.exception(
                    "==> Error al procesar postulación ID: %s - Error: %s",
                    postulation_id.id,
                    str(e)
                )
                postulation_id.message_post(
                    body=_(f'Error al marcar la postulación como rechazada: {str(e)}')
                )

        logging.warning(
            "==> Finalizando cron de marcar postulaciones como rechazadas. "
            "Procesados: %s registros", counter
        )

    @api.model
    def _cron_benefit_expiration_reminder(self):
        """ 
            This function allows you to notify by email if the application is non accepted.
        """
        logging.warning("==> Iniciando cron de recordatorios de expiración de beneficios ...")

        five_days_prior: datetime = fields.datetime.now() - timedelta(days=5)
        # Get all postulations with more than 5 days of notified
        postulations_ids = self.search([
            ('notification_date', '<=', five_days_prior),
            ('state', '=', 'notified')
        ])

        logging.warning(
            "==> Se encontraron %d postulaciones para enviar recordatorios",
            len(postulations_ids)
        )

        counter = 0
        rejected_counter = 0

        for postulation in postulations_ids:
            try:
                vat = postulation.partner_id.partner_id.vat
                name = postulation.partner_id.partner_id.name
                reminder_count = postulation.reminder_count

                logging.info(
                    "==> Procesando postulación ID: %s - Empresa: %s-%s - "
                    "Recordatorios enviados: %s",
                    postulation.id, vat, name, reminder_count
                )

                if postulation.reminder_count == 3:
                    logging.info(
                        "==> Postulación ID: %s alcanzó el límite de 3 recordatorios, "
                        "marcando como rechazada",
                        postulation.id
                    )
                    postulation.message_post(
                        body=_(
                            'La postulación se marcó como rechazada dado que se notificó '
                            'recordatorio en tres (3) oportunidades y no se aceptó el beneficio '
                            'por parte de la empresa.'
                        )
                    )
                    postulation.state = 'rejected'
                    rejected_counter += 1
                    logging.info(
                        "==> Postulación ID: %s marcada como rechazada "
                        "por exceso de recordatorios",
                        postulation.id
                    )
                else:
                    next_reminder = postulation.reminder_count + 1
                    logging.info(
                        "==> Enviando recordatorio %d/3 para postulación ID: %s",
                        next_reminder, postulation.id
                    )
                    self.send_reminder_benefit_expiration(postulation)
                    logging.info(
                        "==> Recordatorio enviado exitosamente para "
                        "postulación ID: %s",
                        postulation.id
                    )

                counter += 1

            except Exception as e:
                logging.exception(
                    "==> Error al procesar recordatorio para postulación ID: %s - "
                    "Error: %s",
                    postulation.id,
                    str(e)
                )
                postulation.message_post(
                    body=_(
                        'Error al procesar recordatorio de beneficio: %s'
                    ) % str(e)
                )

        logging.warning(
            "==> Finalizando cron de recordatorios de expiración. "
            "Procesados: %d registros, Rechazados: %d",
            counter,
            rejected_counter
        )

    def send_reminder_benefit_expiration(self,postulation):
        try:
            partner = self.env['res.partner'].search(
                [('id', '=', postulation.partner_id.partner_id.id)]
            )

            access_link = partner._notify_get_action_link('view')
            subject = "Tienes pendiente aceptar tus codigos de barras sin costo"
            template = self.env.ref('rvc.mail_template_notify_reminder_code_benefit')

            email_values = {'subject': subject}
            wizard = self.env['rvc.template.email.wizard']
            wizard.send_mail_with_attachment(
                template=template,
                record=postulation,
                email_values=email_values,
                report_ref='rvc.action_report_rvc',
                attachment_name_template='Oferta_Mercantil_RVC_{partner_vat}.pdf',
                access_link=access_link,
                require_attachment=True
            )

            #sumar una unidad a la cantidad de recordatorios enviados
            #sirve para enviar únicamente 3 recordatorios por postulación.
            postulation.reminder_count += 1

            #actualizar fecha de notificación por la de hoy para que vuelva a 
            #contar otros 5 días antes de notificar
            postulation.write({'notification_date': datetime.now()})

        except Exception as e:
            raise ValidationError(e)

    def attach_OM_2_partner(self, postulation_id):
        """Adjunta la Oferta Mercantil en el tercero (Compañía o individual) que la acepta."""
        if isinstance(postulation_id, int):
            postulation_id = self.browse(postulation_id)
        if not postulation_id or not postulation_id.exists():
            raise UserError("El registro de postulación no existe.")

        postulation_id.ensure_one()

        report_action = self.env.ref('rvc.action_report_rvc')
        pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
            report_action, [postulation_id.id]
        )

        b64_pdf = base64.b64encode(pdf_content)

        attachment = self.env['ir.attachment'].create({
            'name': "Oferta Mercantil RVC.pdf",
            'type': 'binary',
            'datas': b64_pdf,
            'res_model': 'res.partner',
            'res_id': postulation_id.partner_id.partner_id.id
        })

        if attachment:
            return True 
        return False

    def calculate_end_date_colabora(self):
        next_year = fields.Date.today() + relativedelta(years=1)
        self.end_date_colabora = next_year

    def send_notification_benefit(self):
        for benefit_admon in self:
            partner = self.env['res.partner'].search(
                [('id', '=', benefit_admon.partner_id.partner_id.id)]
            )
            if partner and benefit_admon.partner_id.contact_email:
                # notificar Derechos de Identificación
                if benefit_admon.product_id.code == '01':
                    access_link = partner._notify_get_action_link('view')
                    subject = "Beneficio Derechos de Identificación"
                    template = self.env.ref('rvc.mail_template_notify_benefit_codes')

                    email_values = {'subject': subject}
                    wizard = self.env['rvc.template.email.wizard']
                    wizard.send_mail_with_attachment(
                        template=template,
                        record=benefit_admon,
                        email_values=email_values,
                        report_ref='rvc.action_report_rvc',
                        attachment_name_template='Oferta_Mercantil_RVC_{partner_vat}.pdf',
                        access_link=access_link,
                        require_attachment=True
                    )

                    benefit_admon.write({'state': 'notified', 'notification_date': datetime.now()})
                # notificar Logyca / Colabora
                if benefit_admon.product_id.code == '02':
                    access_link = partner._notify_get_action_link('view')
                    subject = "Beneficio Plataforma LOGYCA / COLABORA"
                    template = self.env.ref('rvc.mail_template_notify_benefit_colabora')

                    email_values = {'subject': subject}
                    wizard = self.env['rvc.template.email.wizard']
                    wizard.send_mail_with_attachment(
                        template=template,
                        record=benefit_admon,
                        email_values=email_values,
                        access_link=access_link,
                        require_attachment=True
                    )

                    benefit_admon.write({'state': 'notified', 'notification_date': datetime.now()})

    def get_odoo_url(self):
        return self.env['ir.config_parameter'].sudo().get_param('web.base.url')

    def validate_has_colabora(self):
        for benefit in self:
            benefit._validate_has_colabora(benefit.partner_id.vat)

    def _validate_has_colabora(self, vat):
        """ Valida si la empresa ya tiene colabora.
        En caso de que si, no es apto para ser beneficiario RVC.

        :param vat es el número de identificación de la empresa
        :return True si NO tiene colabora, False si tiene colabora
        """

        bearer_token = self.get_token_colabora_api()

        if bearer_token or bearer_token[0]:

            if self.get_odoo_url() == 'https://logyca.odoo.com':
                url = "https://app-mstransaction-prod.azurewebsites.net/api/Company/GetCompanyWithStatusServiceByNit?compaynNit=%s" % (str(vat))
            else:
                # url = "https://app-mstransaction-release.azurewebsites.net/api/Company/GetCompanyWithStatusServiceByNit?compaynNit=%s" % (str(vat))
                url = "https://app-mstransaction-prod.azurewebsites.net/api/Company/GetCompanyWithStatusServiceByNit?compaynNit=%s" % (str(vat))
                # url = "https://app-mstransaction-dev.azurewebsites.net/api/Company/GetCompanyWithStatusServiceByNit?compaynNit=%s" % (str(vat))
                # url = "https://app-mstransaction-prod.azurewebsites.net/api/Company/GetCompanyWithStatusServiceByNit?compaynNit=%s" % (str(vat))

            headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer %s' % bearer_token}
            print('&&&&&&&', url)
            #Making http get request
            response = requests.get(url, headers=headers, verify=True)
            print('&&&&&&&222', response.status_code)
            if response.status_code == 200:
                result = response.json()
                print('&&&&&&&333', result)
                if result.get('resultMessage'):
                    raise ValidationError(\
                        _('¡Validación!  %s ') % str(result.get('resultMessage')))
                if 'resultObject' in result:
                    raise ValidationError(('¡Estado Actual LOGYCA / COLABORA!  %s ') % str(result.get('resultObject')['companyName']) + ' Nivel: ' +
                                        str(result.get('resultObject')['currentLevel']) + ' Fecha Incial: ' +  str(result.get('resultObject')['initialDate'])[0:10] + ' Fecha Final: ' +
                                        str(result.get('resultObject')['endDate'])[0:10])
                response.close()
            else:
                logging.debug(f" Error en _validate_has_colabora código: =====> {response.status_code}")
        else:
            raise ValidationError(\
                    _('¡Error de comunicación! Odoo no pudo comunicarse con Logyca/Colabora para verificar si la empresa ya tiene el servicio activo.'))
        return True

    def _get_benefit_name(self):
        benefit_name = ""
        if self.benefit_type == 'codigos':
            benefit_name = "Códigos de Barras"
        elif self.benefit_type == 'colabora':
            benefit_name = "LOGYCA / COLABORA"
        elif self.benefit_type == 'analitica':
            benefit_name = "LOGYCA / ANALÍTICA"    
        return benefit_name

    def action_generate_digital_cards(self):
        cards_list = []

        for i,card in enumerate(self.digital_card_ids, start=0):
            try:
                digital_card = next(self.image_generation(card,i))
                cards_list.append(digital_card)
            except Exception as e:
                logging.exception("====> action_generate_digital_cards =>" + str(e))
                self.message_post(body=_(\
                    'No se pudo generar la tarjeta digital. <strong>Error:</strong> %s' % str(e)))

        return cards_list

    def send_digital_cards_bearer(self, template):
        if self.digital_card_ids:
            cards = self.action_generate_digital_cards()
            counter = 0
            attachments = []
            attachments.append(template.attachment_ids)
            template.write({'attachment_ids': []})

            for i in self.digital_card_ids:
                logging.info(f"counter is ==>{counter}")
                logging.info(f"cards is \n ==>{cards}")
                ir_values = {
                    'name': f"Tarjeta_digital_{i}.JPEG",
                    'type': 'binary',
                    'datas': cards[counter],
                    'store_fname': f"Tarjeta_digital_{i}.JPEG",
                    'mimetype': 'image/jpeg',
                }
                attach_id = self.env['ir.attachment'].create(ir_values)
                logging.info(" Attachment ===> "+ str(attach_id.name))
                template.write({
                    'attachment_ids': [(4, attach_id.id, 0)]
                })
                attachments.append(attach_id)
                counter += 1
                
            partner=self.env['res.partner'].search([('id','=',self.partner_id.partner_id.id)])
            access_link = partner._notify_get_action_link('view')
            logging.info(f"Access link => {access_link}")
            template.with_context(url=access_link).send_mail(self.id, force_send=True)

            for attach_id in attachments:
                attach_id.unlink()

    def image_generation(self, card, i):

        service_offered = card.offered_service_id.name if card.offered_service_id else self.offered_service_id.name
        service_offered_banner =  self.get_banner_digital_card(service_offered)
        base_image_path = get_module_resource('rvc', f'static/img/digital_cards_tmpl/{service_offered_banner}.png')
        image = Image.open(base_image_path)

        # generating QR image
        image2 = Image.open((BytesIO(self.qr_generation(card))))
        (width, height) = (160, 160)
        im_resized = image2.resize((width, height), Image.ANTIALIAS)

        # pasting QR barcode image over digital card
        image.paste(im_resized, (166,134))

        enterprise_name, enterprise_font, ent_txt_padding = self.get_text_style(card.partner_name)
        contact_name, contact_name_font, name_txt_padding = self.get_text_style(str.upper(card.contact_name))
        contact_mobile, contact_mobile_font, mob_txt_padding = self.get_text_style(str.upper(card.contact_mobile))
        contact_mobile, contact_mobile_font, mob_txt_padding = self.get_text_style(str.upper(card.contact_mobile))
        contact_street, contact_street_font, st_txt_padding = self.get_text_style(str.upper(card.street))
        service_offered, service_offered_font, srv_txt_padding = self.get_text_style(str.upper(service_offered))

        image_editable = ImageDraw.Draw(image)
        image_editable.text((125, 392-ent_txt_padding), enterprise_name, font=enterprise_font, fill=(0,0,0,255))
        image_editable.text((125, 472-name_txt_padding), contact_name, font=contact_name_font, fill=(0,0,0,255))
        image_editable.text((125, 552-mob_txt_padding), contact_mobile, font=contact_mobile_font, fill=(0,0,0,255))
        image_editable.text((125, 632-st_txt_padding), contact_street, font=contact_street_font, fill=(0,0,0,255))
        image_editable.text((125, 712-srv_txt_padding), service_offered, font=service_offered_font, fill=(0,0,0,255))
        edited = image.save(f'tmp{i}.png')

        buffered = BytesIO(edited)
        image.save(buffered, format="PNG", optimize=True, progressive=True)
        
        img_str = base64.b64encode(buffered.getvalue())
        self.digital_card_ids[i].digital_card_img = img_str
        image.close()
        image2.close()
        yield img_str

    def qr_generation(self, card):
        import urllib

        # Construir la URL
        data = {
            'name': card.contact_name,
            'work_phone': card.contact_mobile,
            'email': card.contact_email,
            'enterprise': card.partner_name,
            'url': card.url_website,
            'address': card.street,
            'city' : card.city_id.name
        }

        base_url = "https://qrcode.tec-it.com/API/QRCode"

        params = {
            'data': "BEGIN:VCARD\n"
                    "VERSION:3.0\n"
                    "N;CHARSET=UTF-8:{name}\n"
                    "TEL;TYPE=WORK,VOICE:{work_phone}\n"
                    "EMAIL;type=INTERNET;type=WORK;type=pref:{email}\n"
                    "ORG;CHARSET=UTF-8:{enterprise}\n"
                    "URL:{url}\n"
                    "ADR;TYPE=DOM,HOME,POSTAL,PARCEL;CHARSET=UTF-8:;;{address};{city}\n"
                    "LABEL;TYPE=WORK:{address}\n"
                    "END:VCARD".format(**data)
        }

        url = f"{base_url}?{urllib.parse.urlencode(params)}"

        # Codificar la URL en UTF-8
        encoded_url = url.encode('utf-8')



        img = base64.b64encode(requests.get(encoded_url).content)
        card.qr_code = img
        return requests.get(url).content

    def get_banner_digital_card(self, service):
        CATEGORIES = {
            'Alimentos y bebidas': 4,
            'Hospitalaria y farmacéutica': 5,
            'Salud y belleza': 5,
            'Calzado, maletas, bolsos y estuches': 2,
            'Indumentaria, textiles y accesorios': 2,
            'Construcción y servicios relacionados': 3,
            'Equipos electricos e iluminación': 3,
            'Maquinaria, herramientas y equipos industriales': 3,
            'Metalurgia, quimicos , caucho y plasticos': 3,
            'Muebles y mobiliario': 3,
            'Piezas de vehículos y transportes': 3,
            'Animales vivos y productos para mascotas': 1,
            'Arte y manualidades, instrumentos musicales y entretenimiento': 1,
            'Artículos de oficina y escolares, empaque y equipos de servicios': 1,
            'Artículos deportivos': 1,
            'Electronicos': 1,
            'Juegos y juguetes': 1,
            'Suministros para el hogar, jardín y materiales de construcción': 1,
            'Bienes raíces, alquiler y arrendamiento': 6,
            'Servicios comerciales y profesionales': 6,
            'Servicios de arte, entretenimiento y recreación': 6,
            'Servicios de educación Y capacitación': 6,
            'Servicios de informática y comunicación': 6,
            'Servicios de transporte y logística': 6,
            'Servicios financieros': 6,
            'Servicios públicos y de gestión ambiental': 6,
            'Servicios relacionados con el turismo y los viajes': 6,
            'Tecnologías de información y comunicación': 6,
            'Servicios sociales y relacionados con la salud': 6
        }
        return CATEGORIES.get(service, 0) # el valor por defecto es 0 para Categoría OTROS.

    def get_text_style(self, text):
        from PIL import ImageFont
        txt_padding = 0

        if len(text) >= 60:
            wrapped = textwrap.wrap(str.upper(text), width=33, max_lines=2)
        else:
            wrapped = textwrap.wrap(str.upper(text), width=28, max_lines=2)

        font = ImageFont.truetype(get_module_resource('rvc', 'static/font/arial.ttf'), 17)

        if len(wrapped) >= 2:
            font = ImageFont.truetype(get_module_resource('rvc', 'static/font/arial.ttf'), 15)
            txt_padding = 8

        text = '\n'.join(wrapped)

        return text, font, txt_padding

    def _send_assing_crece_mype(self):
        for benefit_admon in self:
            partner=self.employee_id
            if partner and benefit_admon.email_employee:
                if benefit_admon.product_id.benefit_type == 'crece_mype':
                    access_link = partner._notify_get_action_link('view')
                    subject = "Asignacion de caso LOGYCA/CRECEMYPE: Correo electronico"
                    template = self.env.ref('rvc.mail_template_notify_crecemype')
                    template.with_context(url=access_link).send_mail(benefit_admon.id, force_send=False, email_values={'subject': subject})

    def action_application_done(self):
        for benefit_application in self:
            view_id = self.env.ref('rvc.rvc_template_email_wizard_mype_form').id,
            return {
                'name':_("Confirmar"),
                'view_mode': 'form',
                'view_id': view_id,
                'view_type': 'form',
                'res_model': 'rvc.template.email.wizard',
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
                'domain': '[]'
            }