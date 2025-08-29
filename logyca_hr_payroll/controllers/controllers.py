# -*- coding: utf-8 -*-
# from odoo import http


# class lavishHrPayroll(http.Controller):
#     @http.route('/lavish_hr_payroll/lavish_hr_payroll/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/lavish_hr_payroll/lavish_hr_payroll/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('lavish_hr_payroll.listing', {
#             'root': '/lavish_hr_payroll/lavish_hr_payroll',
#             'objects': http.request.env['lavish_hr_payroll.lavish_hr_payroll'].search([]),
#         })

#     @http.route('/lavish_hr_payroll/lavish_hr_payroll/objects/<model("lavish_hr_payroll.lavish_hr_payroll"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('lavish_hr_payroll.object', {
#             'object': obj
#         })
