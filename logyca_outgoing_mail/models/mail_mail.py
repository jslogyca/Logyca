import logging
import re
from odoo import models, fields, api
from odoo.tools import formataddr, split_email_with_name

_logger = logging.getLogger(__name__)


class MailMail(models.Model):
    _inherit = 'mail.mail'

    def _get_domain_from_reply_to(self, reply_to):
        """
        Extract domain from reply_to field.
        Handles formats like: "Name" <email@domain.com> or email@domain.com
        """
        if not reply_to:
            return None

        domain_match = re.search(r'@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', reply_to)
        if domain_match:
            return domain_match.group(1)
        return None

    def _get_outgoing_server_by_rules(self):
        """
        Select outgoing mail server based on business rules.
        """
        self.ensure_one()
        mail_servers = self.env['ir.mail_server'].search([])
        server_dict = {server.smtp_user: server for server in mail_servers}

        fallback_server = server_dict.get('no-reply@logyca.com')

        if not self.model or not self.res_id:
            _logger.info(
                "Mail without related document, using fallback server: no-reply@logyca.com"
            )
            return fallback_server

        if self.model == 'helpdesk.ticket':
            domain = self._get_domain_from_reply_to(self.reply_to)

            # Check for logyca.odoo.com subdomain cases
            if domain == 'logyca.odoo.com' and self.reply_to:
                # Extract the part before @ to check for GS1
                email_part = self.reply_to.split('@')[0].lower()
                if 'gs1' in email_part:
                    selected_server = server_dict.get('web@gs1co.org')
                    _logger.info(
                        "Helpdesk ticket with GS1@logyca.odoo.com, using server: %s",
                        "web@gs1co.org"
                    )
                    return selected_server or fallback_server
                else:
                    selected_server = server_dict.get('web@logyca.com')
                    _logger.info(
                        "Helpdesk ticket with non-GS1@logyca.odoo.com, using server: %s",
                        "web@logyca.com"
                    )
                    return selected_server or fallback_server
            elif domain == 'gs1co.org':
                selected_server = server_dict.get('web@gs1co.org')
                _logger.info(
                    "Helpdesk ticket with gs1co.org domain, using server: %s",
                    "web@gs1co.org"
                )
                return selected_server or fallback_server
            elif domain == 'logyca.com':
                selected_server = server_dict.get('web@logyca.com')
                _logger.info(
                    "Helpdesk ticket with logyca.com domain, using server: %s",
                    "web@logyca.com"
                )
                return selected_server or fallback_server
            else:
                _logger.info(
                    "Helpdesk ticket with unknown/no domain (%s), "
                    "using fallback: no-reply@logyca.com",
                    domain
                )
                return fallback_server

        elif self.model == 'benefit.application':
            selected_server = server_dict.get('no-reply@gs1co.org')
            _logger.info("Benefit application, using server: %s", "no-reply@gs1co.org")
            return selected_server or fallback_server

        else:
            # Handle logyca.odoo.com cases for non-ticket models
            domain = self._get_domain_from_reply_to(self.reply_to)
            if domain == 'logyca.odoo.com' and self.reply_to:
                # Extract the part before @ to check for GS1
                email_part = self.reply_to.split('@')[0].lower()
                if 'gs1' in email_part:
                    selected_server = server_dict.get('no-reply@gs1co.org')
                    _logger.info(
                        "Non-ticket document with GS1@logyca.odoo.com, using server: %s",
                        "no-reply@gs1co.org"
                    )
                    return selected_server or fallback_server
                else:
                    selected_server = server_dict.get('no-reply@logyca.com')
                    _logger.info(
                        "Non-ticket document with non-GS1@logyca.odoo.com, using server: %s",
                        "no-reply@logyca.com"
                    )
                    return selected_server or fallback_server
            else:
                _logger.info(
                    "Document type %s not matching specific rules, "
                    "using fallback: no-reply@logyca.com",
                    self.model
                )
                return fallback_server

    def _update_email_from_and_server(self):
        """
        Applies the routing rules to a set of mails.
        """
        for mail in self:
            selected_server = mail._get_outgoing_server_by_rules()
            if selected_server and mail.mail_server_id != selected_server:
                original_name = split_email_with_name(mail.email_from)[0]
                new_email_from = formataddr(
                    (
                        original_name or selected_server.name,
                        selected_server.smtp_user,
                    )
                )

                update_vals = {
                    'mail_server_id': selected_server.id,
                    'email_from': new_email_from,
                }
                mail.write(update_vals)
                _logger.info(
                    "Mail ID %s: Server updated to %s, sender set to %s",
                    mail.id,
                    selected_server.name,
                    new_email_from,
                )

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create to set the correct server and sender when creating email.
        """
        mails = super().create(vals_list)
        for mail in mails:
            if not mail.mail_server_id:
                mail._update_email_from_and_server()
        return mails

    def write(self, vals):
        """
        Override write to update server if relevant fields change.
        """
        result = super().write(vals)
        if any(field in vals for field in ['model', 'res_id', 'reply_to']):
            for mail in self:
                if not vals.get('mail_server_id'):
                    mail._update_email_from_and_server()
        return result
