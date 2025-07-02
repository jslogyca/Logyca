# -*- coding: utf-8 -*-
# ############################################################################
#
#     Metclouds Technologies Pvt Ltd
#
#     Copyright (C) 2022-TODAY Metclouds Technologies(<https://metclouds.com>)
#     Author: Metclouds Technologies(<https://metclouds.com>)
#
#     You can modify it under the terms of the GNU LESSER
#     GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#     You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#     (LGPL v3) along with this program.
#     If not, see <http://www.gnu.org/licenses/>.
#
# ############################################################################

import logging
import json
import io
from xlsxwriter import workbook

from odoo import fields, models, tools, api

from datetime import datetime, date, timedelta
from odoo.http import request
from odoo.tools import date_utils
from odoo.exceptions import UserError, ValidationError

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


_logger = logging.getLogger(__name__)


class DailySalesReportWizard(models.TransientModel):

    _name = "daily.sales.report.wizard"
    _description = "Daily Sales Report wizard"

    from_date = fields.Date(string="Start Date", default=date.today()-timedelta(days=7))
    to_date = fields.Date(string="End Date")
    current_session = fields.Char(readonly=True, default="0")
    session_date = fields.Date(readonly=True, default=date.today())
    # company_ids = fields.Many2many('res.company', string='Companies')

    product_id = fields.Integer(string="ID", readonly=True)
    product_name = fields.Char(string='Name', readonly=True)
    sunday = fields.Integer(string="Sunday", readonly=True)
    monday = fields.Integer(string="Monday", readonly=True)
    tuesday = fields.Integer(string="Tuesday", readonly=True)
    wednesday = fields.Integer(string="Wednesday", readonly=True)
    thursday = fields.Integer(string="Thursday", readonly=True)
    friday = fields.Integer(string="Friday", readonly=True)
    saturday = fields.Integer(string="Saturday", readonly=True)

    total = fields.Integer(string="Total", readonly=True)

    @api.onchange('from_date')
    def onchange_from_date(self):
        if self.from_date:
            if((date.today() - self.from_date).days > 180):
                raise ValidationError(
                    "Only last 180 days data can be checked. %s is over 180 days" % self.from_date)

    @api.onchange('to_date')
    def onchange_to_date(self):
        if self.to_date:
            if(self.to_date > date.today()):
                raise ValidationError(
                    "Future date can't be selected")

    @api.onchange('from_date','to_date')
    def onchange_from_date_to_date(self):
        if self.from_date and self.to_date:
            if (self.from_date > self.to_date):
                raise ValidationError(
                    "Please select dates correctly!!!")
        if not self.from_date:
            self.from_date = (date.today()-timedelta(days=180)).isoformat()

    def get_daily_sales_report_wizard(self):

        if not self.from_date and not self.to_date:
            raise ValidationError(
                "Dates required")

        from_date = self.from_date if self.from_date else date.today()
        to_date = self.to_date if self.to_date else date.today()

        request.session['from_date'] = from_date
        request.session['to_date'] = to_date
        request.session['print_report'] = False

        db_data = self.env['daily.sales.report.wizard'].search([
            '&', '&', ('current_session', '=',
                       request.session['session_token']),
            ('from_date', '=', self.from_date),
            ('to_date', '=', self.to_date if self.to_date else date.today())])

        if not db_data:
            self._cr.execute("""DELETE FROM daily_sales_report_wizard WHERE current_session = '0' OR current_session = '%s'  OR session_date < '%s'""" % (
                request.session['session_token'], date.today()))

            record_ids = self._get_data()

            for record in record_ids:
                self._cr.execute("""
                    INSERT INTO daily_sales_report_wizard (product_id, product_name, 
                        sunday, monday, tuesday, wednesday, 
                        thursday, friday, saturday, total, from_date, to_date, current_session, session_date,
                        create_date, create_uid, write_date, write_uid)
                    VALUES (%d, '%s', %d, %d, %d, %d, %d, %d, %d, %d, '%s', '%s', '%s', '%s', NOW(), %d, NOW(), %d)""" % (
                    record['product_id'],  record['product_name'].replace(
                        "'", "''"),
                    record['sunday'], record['monday'],
                    record['tuesday'], record['wednesday'],
                    record['thursday'], record['friday'],
                    record['saturday'], record['total'],
                    from_date, to_date,
                    request.session['session_token'],
                    date.today(),
                    self.env.user.id,
                    self.env.user.id)
                )

        return {
            'type': 'ir.actions.act_window',
            'name': 'Daily Product Sales Report From ' + from_date.strftime("%m/%d/%Y") + ' - To ' + to_date.strftime("%m/%d/%Y"),
            'res_model': 'daily.sales.report.wizard',
            'view_type': 'tree',
            'view_mode': 'tree',
            'domain': [('current_session', '=', request.session['session_token'])],
            'target': 'new',
            'help':  '''<p> No data to show!!!
                        </p>'''
        }

    def _get_data(self):

        _logger.info('Create a %s with vals %s', self.from_date, self.to_date)

        sale_order_line_data = self.env['sale.order.line'].search(
            [('order_id.state', '!=', 'cancel')])

        if self.from_date and self.to_date:
            order_list = list(filter(lambda
                                     x: x.order_id.date_order.date() >= self.from_date and x.order_id.date_order.date() <= self.to_date,
                                     sale_order_line_data))
            result = self._get_daywise_report_data(order_list)

        elif not self.from_date and self.to_date:
            order_list = list(filter(lambda
                                     x: x.order_id.date_order.date() <= self.to_date,
                                     sale_order_line_data))
            result = self._get_daywise_report_data(order_list)
        elif self.from_date and not self.to_date:
            order_list = list(filter(lambda
                                     x:  x.order_id.date_order.date() >= self.from_date,
                                     sale_order_line_data))
            result = self._get_daywise_report_data(order_list)
        else:
            result = self._get_daywise_report_data(sale_order_line_data)

        return result

    def _get_daywise_report_data(self, order):

        filtered_order = list(order)
        result = []
        product_dict = {}
        total = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, }
        for rec in filtered_order:
            days = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, }
            days[rec.order_id.date_order.weekday()] = rec.product_uom_qty
            total[rec.order_id.date_order.weekday()] += rec.product_uom_qty
            if (rec.product_id not in product_dict):
                p_name = rec.name
                if request.session['print_report']:
                    p_name = p_name if (len(p_name) < 90) else p_name[0:90]
                product_dict[rec.product_id] = {
                    'product_id': rec.product_id.id,
                    'product_name': p_name,
                    'sunday': int(days[6]),
                    'monday': int(days[0]),
                    'tuesday': int(days[1]),
                    'wednesday': int(days[2]),
                    'thursday': int(days[3]),
                    'friday': int(days[4]),
                    'saturday': int(days[5]),
                    'total': rec.product_uom_qty,
                }
            else:
                day_str = rec.order_id.date_order.strftime('%A').lower()
                product_dict[rec.product_id][day_str] += days[rec.order_id.date_order.weekday()]
                product_dict[rec.product_id]['total'] += rec.product_uom_qty

        if request.session['print_report'] and product_dict:
            product_dict['total'] = {
                'product_id': 0,
                'product_name': "",
                'sunday': int(total[6]),
                'monday': int(total[0]),
                'tuesday': int(total[1]),
                'wednesday': int(total[2]),
                'thursday': int(total[3]),
                'friday': int(total[4]),
                'saturday': int(total[5]),
                'total': sum(total.values()),
            }
        request.session['print_report'] = False
        result = list(product_dict.values())
        return result

    def get_daily_sales_report_print(self):

        request.session['print_report'] = True
        request.session['from_date'] = self.from_date
        request.session['to_date'] = self.to_date if self.to_date else date.today()

        record_ids = self._get_data()

        datas = {
            'ids': self,
            'model': 'daily.sales.report.wizard',
            'form': record_ids,
            'start_date': request.session['from_date'],
            'end_date': request.session['to_date'],
        }
        return self.env.ref('mt_daywise_product_sales_report.action_report_daywise_saleorder').report_action([], data=datas)

    def get_daily_sales_excel_report(self):
        request.session['from_date'] = self.from_date
        request.session['to_date'] = self.to_date if self.to_date else date.today()
        request.session['print_report'] = True

        xlxs_record = self._get_data()

        datas = {
            'ids': self,
            'model': 'daily.sales.report.wizard',
            'form': xlxs_record,
            'start_date': request.session['from_date'],
            'end_date': request.session['to_date'],
        }
        return {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'data': {'model': 'daily.sales.report.wizard',
                     'output_format': 'xlsx',
                     'options': json.dumps(datas, default=date_utils.json_default),
                     'report_name': 'Daywise_Product_Sales_Report',
                     },
        }

    def print_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        cell_format = workbook.add_format({'font_size': '12px', })
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '20px'})
        txt = workbook.add_format({'font_size': '10px', 'align': 'center'})
        no_data = workbook.add_format({'font_size': '12px', 'align': 'center', 'valign': 'vcenter'})
        sheet.merge_range('C2:K3', 'Daywise Product Sales Report', head)

        if data['start_date'] and data['end_date']:
            sheet.write('D6', 'From:', cell_format)
            sheet.write('E6', data['start_date'], txt)
            sheet.write('G6', 'To:', cell_format)
            sheet.write('H6', data['end_date'], txt)
        format1 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bg_color': '#f5f9ff', 'border': 1})
        format2 = workbook.add_format(
            {'font_size': 10, 'align': 'left', 'bg_color': '#f5f9ff', 'border': 1})
        format3 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bold': True, 'bg_color': '#6BA6FE', 'border': 1})
        format4 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bold': True, 'bg_color': '#b6d0fa', 'border': 1})

        row_number = 7
        column_number = 2

        column_data = {0: ('Product Name', 'product_name', 'C:C', 30),
                    1: ('Sunday', 'sunday', 'D:D', 10),
                    2: ('Monday', 'monday', 'E:E', 10),
                    3: ('Tuesday', 'tuesday', 'F:F', 10),
                    4: ('Wednesday', 'wednesday', 'G:G', 10),
                    5: ('Thursday', 'thursday', 'H:H', 10),
                    6: ('Friday', 'friday', 'I:I', 10),
                    7: ('Saturday', 'saturday', 'J:J', 10),
                    8: ('Total', 'total', 'K:K', 10), }

        for col_head, col_name, col_pos, col_width in column_data.values():
            sheet.write(row_number, column_number, col_head, format4)
            sheet.set_column(col_pos, col_width)
            column_number += 1

        if not data['form']:
            sheet.merge_range('C9:K11', 'No Data', no_data)
        else:
            for val in data['form']:
                column_number = 2
                row_number += 1

                for col_head, col_name, col_pos, col_width in column_data.values():
                    d_format = format2 if col_name == 'product_name' else (
                        format3 if col_name == 'total' else format1)

                    sheet.write(row_number, column_number, val[col_name], d_format)
                    sheet.set_column(col_pos, col_width)
                    column_number += 1

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
