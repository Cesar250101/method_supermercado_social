# -*- coding: utf-8 -*-
from odoo import http

# class MethodSupermercadoSocial(http.Controller):
#     @http.route('/method_supermercado_social/method_supermercado_social/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/method_supermercado_social/method_supermercado_social/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('method_supermercado_social.listing', {
#             'root': '/method_supermercado_social/method_supermercado_social',
#             'objects': http.request.env['method_supermercado_social.method_supermercado_social'].search([]),
#         })

#     @http.route('/method_supermercado_social/method_supermercado_social/objects/<model("method_supermercado_social.method_supermercado_social"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('method_supermercado_social.object', {
#             'object': obj
#         })