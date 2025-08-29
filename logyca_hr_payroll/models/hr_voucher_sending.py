# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.modules.registry import Registry
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import odoo
import base64
import threading
from datetime import datetime
import logging
from typing import List
from contextlib import contextmanager
from odoo.tools import frozendict
_logger = logging.getLogger(__name__)
#---------------------------Modelo para generar Archivo plano de pago de nómina-------------------------------#
BATCH_SIZE = 50

class mail_mail(models.Model):
    _inherit = 'mail.mail'

    payroll_voucher = fields.Boolean(string='Email para comprobante de nómina')
    payroll_voucher_id = fields.Many2one('hr.voucher.sending', string='Ejecución comprobantes de nómina')

class hr_voucher_sending_failed(models.Model):
    _name = 'hr.voucher.sending.failed'
    _description = 'Ejecución comprobantes de nómina Fallidos'
    
    voucher_id = fields.Many2one('hr.voucher.sending', 'Ejecución comprobantes')
    payslip_id = fields.Many2one('hr.payslip',string='Nómina')    
    employee_id = fields.Many2one(related='payslip_id.employee_id', string='Empleado')
    description = fields.Char('Mensaje')

class PayslipVoucherSending(models.Model):
    _name = 'hr.voucher.sending'
    _description = 'Ejecución comprobantes de nómina'

    send_type = fields.Selection([('send', 'Enviar por correo electrónico')], string='Proceso', default='send',required=True)
    subject = fields.Char(required=True)
    description = fields.Text(string='Cuerpo del correo') 
    generation_type = fields.Selection([
        ('lote', 'Por lote'),
        ('individual', 'Por Empleado')
    ], required=True, default='lote')
    payslip_run_id = fields.Many2one('hr.payslip.run', string='Payslip Batch')
    employee_id = fields.Many2one('hr.employee',string='Empleado')    
    payslip_id = fields.Many2one('hr.payslip',string='Nómina', domain="[('employee_id','=',[employee_id])]")
    vouchers_failed_ids = fields.One2many('hr.voucher.sending.failed', 'voucher_id', string='Failed Vouchers')
    mail_mail_ids = fields.One2many('mail.mail','payroll_voucher_id','Correos electrónicos')
    txt_status_process = fields.Text(string='Estado del proceso')
    mail_mail_count = fields.Integer(string='Total Correos', compute='_compute_mail_counts')
    mail_mail_sent_count = fields.Integer(string='Enviados', compute='_compute_mail_counts')
    mail_mail_failed_count = fields.Integer(string='Fallidos', compute='_compute_mail_counts')

    @api.depends('mail_mail_ids', 'mail_mail_ids.state')
    def _compute_mail_counts(self):
        for record in self:
            record.mail_mail_count = len(record.mail_mail_ids)
            record.mail_mail_sent_count = len(record.mail_mail_ids.filtered(lambda m: m.state == 'sent'))
            record.mail_mail_failed_count = len(record.mail_mail_ids.filtered(lambda m: m.state == 'exception'))

    @contextmanager
    def _get_new_env(self):
        """Create a new environment with a new cursor."""
        registry = Registry(self.env.cr.dbname)
        with registry.cursor() as new_cr:
            new_env = api.Environment(new_cr, self.env.uid, self.env.context)
            try:
                yield new_env
            except Exception as e:
                new_cr.rollback()
                _logger.error(f"Transaction failed: {str(e)}")
                raise
            else:
                new_cr.commit()

    @api.depends('mail_mail_ids', 'mail_mail_ids.state')
    def _compute_mail_counts(self):
        for record in self:
            record.mail_mail_count = len(record.mail_mail_ids)
            record.mail_mail_sent_count = len(record.mail_mail_ids.filtered(lambda m: m.state == 'sent'))
            record.mail_mail_failed_count = len(record.mail_mail_ids.filtered(lambda m: m.state == 'exception'))

    def _create_pdf_attachment(self, env, payslip, pdf_content: bytes) -> int:
        """Create an attachment for the payslip PDF."""
        pdf_name = f"{payslip.struct_id.name} - {payslip.employee_id.name} - {payslip.date_to}.pdf"
        attachment_data = {
            'name': f"Comprobante_nomina_{payslip.employee_id.work_contact_id.vat}_{payslip.name}.pdf",
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_name': pdf_name,
            'store_fname': pdf_name,
            'res_model': 'hr.payslip',
            'res_id': payslip.id
        }
        return env['ir.attachment'].create(attachment_data).id

    def _prepare_email_values(self, payslip, attachment_id: int) -> dict:
        """Prepare email values for sending."""
        employee = payslip.employee_id
        partner_id = employee.work_contact_id.id if employee.work_contact_id else False
        if not partner_id:
            _logger.warning(f"Employee {employee.name} does not have a contact (work_contact_id) configured")
            
        message = f"""
            Estimado {employee.name}<br/><br/>
            Adjunto encontrará la información de la última liquidación y pago de su nómina.<br/><br/><br/>
            Por favor no responda este correo, esto es un mensaje automático.
        """
        
        return {
            'subject': self.subject,
            'email_to': employee.personal_email,
            'email_from': self.env.user.email,
            'body_html': message.encode('utf-8'),
            'payroll_voucher': True,
            'payroll_voucher_id': self.id,
            'attachment_ids': [(6, 0, [attachment_id])],
            'recipient_ids': [(6, 0, [partner_id])] if partner_id else [],
            'model': 'hr.payslip',
            'res_id': payslip.id,
        }

    def _process_payslip(self, env, payslip_id: int) -> None:
        """Process a single payslip and send email."""
        try:
            payslip = env['hr.payslip'].browse(payslip_id)
            
            if not payslip.employee_id.personal_email:
                raise UserError(
                    f"El empleado {payslip.employee_id.name} no tiene un correo electrónico personal configurado"
                )

            report = payslip.struct_id.report_id
            pdf_content, _ = env['ir.actions.report']._render_qweb_pdf(report, payslip.id)
            
            with env.cr.savepoint():
                attachment_id = self._create_pdf_attachment(env, payslip, pdf_content)
                email_vals = self._prepare_email_values(payslip, attachment_id)
                email = env['mail.mail'].create(email_vals)
                email.send()

        except Exception as e:
            env.cr.rollback()
            error_vals = {
                'voucher_id': self.id,
                'payslip_id': payslip.id,
                'description': str(e)
            }
            env['hr.voucher.sending.failed'].create(error_vals)
            _logger.error(f"Error processing payslip {payslip.id}: {str(e)}")

    def _process_batch(self, payslip_ids: List[int]) -> None:
        """Process a batch of payslips with a new environment."""
        with self._get_new_env() as new_env:
            _logger.info(f'Processing batch of {len(payslip_ids)} payslips')
            for payslip_id in payslip_ids:
                self._process_payslip(new_env, payslip_id)

    def _chunk_payslips(self, payslips):
        for i in range(0, len(payslips), BATCH_SIZE):
            yield payslips[i:i + BATCH_SIZE].ids

    def generate_voucher(self):
        self.env.flush_all()
        self.vouchers_failed_ids.unlink()
        start_time = datetime.now()

        try:
            if self.generation_type == 'lote':
                payslips = self.env['hr.payslip'].search([
                    ('payslip_run_id', '=', self.payslip_run_id.id)
                ])
                if not payslips:
                    raise UserError("No se encontraron nóminas en el lote seleccionado.")

                for chunk in self._chunk_payslips(payslips):
                    self._process_batch(chunk)
            else:
                if not self.payslip_id:
                    raise UserError("Seleccione una hoja de país para el procesamiento individual.")
                self._process_batch([self.payslip_id.id])

        except Exception as e:
            _logger.error(f"Error in voucher generation: {str(e)}")
            raise UserError(f"Error al generar Correos: {str(e)}")

        finally:
            process_time = (datetime.now() - start_time).total_seconds() / 60
            _logger.info(f"Voucher generation completed in {process_time:.2f} minutes")

    def generate_voucher_failed(self):
        """Regenerate failed vouchers."""
        if not self.vouchers_failed_ids:
            raise UserError("No hay comprobantes fallidos para procesar")

        payslips = self.env['hr.payslip'].search([
            ('id', 'in', self.vouchers_failed_ids.payslip_id.ids)
        ])
        
        self.vouchers_failed_ids.unlink()
        start_time = datetime.now()

        try:
            for chunk in self._chunk_payslips(payslips):
                self._process_batch(chunk)

        except Exception as e:
            _logger.error(f"Error in failed voucher regeneration: {str(e)}")
            raise UserError(_(f"Error regenerating failed vouchers: {str(e)}"))

        finally:
            process_time = (datetime.now() - start_time).total_seconds() / 60
            _logger.info(f"Failed voucher regeneration completed in {process_time:.2f} minutes")




    
    
