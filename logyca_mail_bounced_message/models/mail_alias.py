# -*- coding: utf-8 -*-
from markupsafe import Markup
from odoo import models, _

class Alias(models.Model):
    _inherit = 'mail.alias'

    def _get_alias_invalid_body(self, message_dict):
        """
        Genera el cuerpo del correo electrónico de rebote devuelto cuando el alias está
        configurado incorrectamente (por ejemplo, un error en alias_defaults).
        """
        content = Markup(
            _(
            "La dirección %(alias_display_name)s no pudo aceptar el correo electrónico anterior. "
            "Por favor, tenga en cuenta que si este es un hilo de correo externo a nuestro sistema "
            "de tickets, debe enviar un correo aparte para la creación de su caso."
            )
        ) % {
            'alias_display_name': self.display_name,
        }
        return self.env['ir.qweb']._render('mail.mail_bounce_alias_security', {
            'body': Markup('<p>%(header)s,<br /><br />%(content)s<br /><br />%(regards)s</p>') % {
                'content': content,
                'header': _('Apreciado remitente'),
                'regards': _('Saludos cordiales'),
            },
            'message': message_dict
        }, minimal_qcontext=True)
