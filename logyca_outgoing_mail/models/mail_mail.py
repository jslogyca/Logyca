import logging
import re
from odoo import models, fields, api

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

        # Search for @domain.com pattern in reply_to
        domain_match = re.search(r'@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', reply_to)
        if domain_match:
            return domain_match.group(1)
        return None

    def _get_outgoing_server_by_rules(self):
        """
        Select outgoing mail server based on business rules.
        """
        # Get all configured mail servers
        mail_servers = self.env['ir.mail_server'].search([])
        server_dict = {server.smtp_user: server for server in mail_servers}

        # Default fallback server
        fallback_server = server_dict.get('no-reply@logyca.com')

        # If no related model, use fallback
        if not self.model or not self.res_id:
            _logger.info(
                "Mail without related document, using fallback server: "
                "no-reply@logyca.com"
            )
            return fallback_server

        # Check if it's a helpdesk ticket
        if self.model == 'helpdesk.ticket':
            # Extract domain from reply_to
            domain = self._get_domain_from_reply_to(self.reply_to)

            if domain == 'gs1co.org':
                selected_server = server_dict.get('web@gs1co.org')
                _logger.info(
                    "Helpdesk ticket with gs1co.org domain, "
                    "using server: %s", "web@gs1co.org"
                )
                return selected_server or fallback_server

            elif domain == 'logyca.com':
                selected_server = server_dict.get('web@logyca.com')
                _logger.info(
                    "Helpdesk ticket with logyca.com domain, "
                    "using server: %s", "web@logyca.com"
                )
                return selected_server or fallback_server

            else:
                _logger.info(
                    "Helpdesk ticket with unknown/no domain (%s), "
                    "using fallback server: no-reply@logyca.com",
                    domain
                )
                return fallback_server

        # Check if it's a benefit application
        elif self.model == 'benefit.application':
            selected_server = server_dict.get('no-reply@gs1co.org')
            _logger.info("Benefit application, using server: %s", "no-reply@gs1co.org")
            return selected_server or fallback_server

        # For any other document type
        else:
            _logger.info(
                "Document type %s not matching specific rules, "
                "using fallback server: no-reply@logyca.com",
                self.model
            )
            return fallback_server

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create to set the correct server when creating email.
        """
        mails = super().create(vals_list)

        for mail in mails:
            if not mail.mail_server_id:
                selected_server = mail._get_outgoing_server_by_rules()
                if selected_server:
                    mail.mail_server_id = selected_server.id
                    _logger.info(
                        "Mail ID %s: Server automatically set to %s",
                        mail.id,
                        selected_server.smtp_user,
                    )

        return mails

    def write(self, vals):
        """
        Override write to update server if relevant fields change.
        """
        result = super().write(vals)

        # If model, res_id or reply_to are updated, recalculate server
        if any(field in vals for field in ['model', 'res_id', 'reply_to']):
            for mail in self:
                if not vals.get('mail_server_id'):  # Only if not manually setting server
                    selected_server = mail._get_outgoing_server_by_rules()
                    if selected_server and mail.mail_server_id != selected_server:
                        mail.mail_server_id = selected_server.id
                        _logger.info(
                            "Mail ID %s: Server updated to %s",
                            mail.id,
                            selected_server.smtp_user,
                        )

        return result
