# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import date_utils

import base64


class AccountCertificationReportWizard(models.TransientModel):
    _name = 'account.certification.report.wizard'
    _description = 'Account Certification Report Wizard'

    partner_ids = fields.Many2many('res.partner', string="Partners")
    # date_range_id = fields.Many2one("date.range")
    company_id = fields.Many2one('res.company',
                                 string='Company',
                                 default=lambda self: self.env.company)
    date_from = fields.Date(string='Date from')
    date_to = fields.Date(string='Date to')
    date = fields.Date(string='Date')
    default_rep_id = fields.Many2one('config.certification.report',
                                     string='Report Default')

    def _clear_table(self):
        self._cr.execute(' DELETE FROM account_certification_header_line ')
        self._cr.execute(' DELETE FROM account_certification_header ')

    def do_report(self):
        self._clear_table()
        if not self.partner_ids:
            raise ValidationError(_('No Partner configured!'))
        if not self.default_rep_id.tax_ids:
            raise ValidationError(_('No taxes configured!'))
        if self.default_rep_id.by_city and not self.default_rep_id.city_id:
            raise ValidationError(_('You must set a default city!'))

        filename = _(f'{self.default_rep_id.name.replace(" ", "_")}_'
                     f'{self.date_from}_to_{self.date_to}')

        for partner in self.partner_ids:
            date = fields.Date.context_today(self)
            partner_filename = f'{filename}_' \
                               f'{partner.name.replace(" ", "_")}_' \
                               f'{partner.vat}.pdf'

            header_obj = self.env['account.certification.header']
            header_id = header_obj.create({
                'date_from': self.date_from,
                'date_to': self.date_to,
                'date': self.date,
                'partner_id': partner.id,
                'company_id': self.company_id.id,
                'date_expe': date,
                'by_city': self.default_rep_id.by_city,
                'default_rep_id': self.default_rep_id.id,
                'note': self.default_rep_id.note,
                'file_name': partner_filename,
                'currency_id': self.company_id.currency_id.id,
            })

            if self.default_rep_id.by_city:
                consulta = f"""
                    INSERT INTO
                        account_certification_header_line(
                            header_id,
                            tax_id,
                            city_id,
                            partner_id,
                            account_id,
                            amount,
                            base,
                            tax_percent)
                        SELECT
                            {header_id.id} AS header_id,
                            t.id as tax_id,
                            CASE
                                WHEN
                                    m.city_id IS NULL
                                THEN
                                    '{self.default_rep_id.city_id.id}'
                                ELSE
                                    m.city_id
                            END AS city_id,
                            l.partner_id AS partner_id,
                            l.account_id AS account_id,
                            sum(l.credit) AS amount,
                            (sum(l.credit)/(abs(t.amount)/100)) as base,
                            round(t.amount, 2) AS tax_percent
                        FROM account_move_line l
                            INNER JOIN account_tax t ON t.id=l.tax_line_id
                            INNER JOIN account_move m ON m.id=l.move_id
                        WHERE
                            l.date BETWEEN '{self.date_from}'
                                AND '{self.date_to}'
                            AND tax_line_id IN
                                {tuple(self.default_rep_id.tax_ids.ids)}
                            AND l.partner_id = {partner.id}
                            AND m.state='posted'
                        GROUP BY
                            t.id,
                            m.city_id,
                            l.partner_id,
                            l.account_id
                    """
            else:
                print('CONSULTA /////////')
            #     consulta = f"""
            #         INSERT INTO
            #             account_certification_header_line(
            #                 header_id,
            #                 tax_id,
            #                 city_id,
            #                 partner_id,
            #                 account_id,
            #                 amount,
            #                 base,
            #                 tax_percent)
            #             SELECT {header_id.id} as header_id,
            #                 t.id as tax_id,
            #                 pp.city_id AS city_id,
            #                 l.partner_id as partner_id,
            #                 l.account_id as account_id,
            #                 sum(l.credit) as amount,
            #                 (sum(l.credit)/(abs(t.amount)/100)) as base,
            #                 round(t.amount,2) as tax_percent
            #             FROM account_move_line l
            #                 INNER JOIN account_tax t ON t.id=l.tax_line_id
            #                 INNER JOIN account_move m ON m.id=l.move_id
            #                 INNER JOIN res_company c ON c.id=m.company_id
            #                 INNER JOIN res_partner pp ON pp.id=c.partner_id
            #             WHERE
            #                 l.date BETWEEN '{self.date_from}'
            #                     AND '{self.date_to}'
            #                 AND tax_line_id IN
            #                     {tuple(self.default_rep_id.tax_ids.ids)}
            #                 AND l.partner_id = {partner.id}
            #                 AND m.state='posted'
            #             GROUP BY
            #                 t.id,
            #                 pp.city_id,
            #                 l.partner_id,
            #                 l.account_id
            #         """

            # self.env.cr.execute(consulta)

            consulta_rte = f"""
                INSERT INTO
                    account_certification_header_line(
                        header_id,
                        tax_id,
                        city_id,
                        partner_id,
                        account_id,
                        amount,
                        base,
                        tax_percent)
                    SELECT {header_id.id} as header_id,
                        null as tax_id,
                        pp.city_id AS city_id,
                        l.partner_id as partner_id,
                        l.account_id as account_id,
                        sum(l.credit) as amount,
                        sum(l.tax_base_amount) as base,
                        0.0 as tax_percent
                    FROM account_move_line l
                        INNER JOIN account_move m ON m.id=l.move_id
                        INNER JOIN res_company c ON c.id=m.company_id
                        INNER JOIN res_partner pp ON pp.id=c.partner_id
                        INNER JOIN account_account ct ON ct.id=l.account_id
                    WHERE
                        l.date BETWEEN '{self.date_from}'
                            AND '{self.date_to}'
                        AND l.account_id IN
                            {tuple(self.default_rep_id.account_ids.ids)}
                        AND l.partner_id = {partner.id}
                        AND m.state='posted'
                    GROUP BY
                        pp.city_id,
                        l.partner_id,
                        l.account_id
                """
            print('CONSULTA', consulta_rte)
            self.env.cr.execute(consulta_rte)


        self._cr.execute(""" SELECT id FROM account_certification_header """)
        result_header_ids = tuple(line[0] for line in self._cr.fetchall())
        headers = self.env['account.certification.header'].browse(
            result_header_ids)

        reports = []
        for header in headers:
            query = f"""
                SELECT
                    id
                FROM
                    account_certification_header_line
                WHERE
                    header_id = {header.id}
                """
            self._cr.execute(query)
            result_line_ids = tuple(line[0] for line in self._cr.fetchall())
            lines = self.env['account.certification.header.line'].browse(
                result_line_ids)
            header.report_line = lines
            base = 0
            amount = 0
            for l in lines:
                base+=l.base
                amount+=l.amount
            header.base = base
            header.amount = amount

            report_template_id = self.env.ref(
                'l10n_co_certification_report.certification_report_pdf'
            )._render_qweb_pdf(header.id)
            data_record = base64.b64encode(report_template_id[0])
            values = {
                'name': str(header.file_name),
                'type': 'binary',
                'datas': data_record,
                'store_fname': data_record,
                'mimetype': 'application/pdf',
                'res_model': 'res.partner',
                'res_id': header.partner_id.id,
                'res_name': header.partner_id.name,
            }
            attach_id = self.env['ir.attachment'].create(values)
            reports.append(attach_id.id)

        self._clear_table()
        url = f"/web/binary/download_zip?" \
              f"model=account.certification.report.wizard&" \
              f"id={self.id}&" \
              f"reports={reports}&" \
              f"filename={filename}"

        return {'type': 'ir.actions.act_url',
                'url': url,
                'target': 'current'}


