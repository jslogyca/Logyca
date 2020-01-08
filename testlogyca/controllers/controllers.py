# -*- coding: utf-8 -*-
from odoo import http

# class testlogyca(http.Controller):
#     @http.route('/testlogyca/testlogyca/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/testlogyca/testlogyca/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('testlogyca.listing', {
#             'root': '/testlogyca/testlogyca',
#             'objects': http.request.env['testlogyca.testlogyca'].search([]),
#         })

#     @http.route('/testlogyca/testlogyca/objects/<model("testlogyca.testlogyca"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('testlogyca.object', {
#             'object': obj
#         })