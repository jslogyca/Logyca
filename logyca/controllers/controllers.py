# -*- coding: utf-8 -*-
# from odoo import http


# class Logyca(http.Controller):
#     @http.route('/logyca/logyca/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/logyca/logyca/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('logyca.listing', {
#             'root': '/logyca/logyca',
#             'objects': http.request.env['logyca.logyca'].search([]),
#         })

#     @http.route('/logyca/logyca/objects/<model("logyca.logyca"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('logyca.object', {
#             'object': obj
#         })
