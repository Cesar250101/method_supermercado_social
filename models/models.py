# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Clientes(models.Model):
    _inherit = 'res.partner'

    grupo_familiar = fields.Integer(string='Tamaño grupo familiar',help='Número de integrantes del grupo familiar')
    hora_retiro = fields.Float(string='Hora de Retiro')
    dia_retiro = fields.Selection(string='Día Retiro', selection=[('lunes', 'Lunes'), 
                                                                  ('martes', 'Martes'),
                                                                  ('miercoles', 'Miercoles'),
                                                                  ('jueves', 'Jueves'),
                                                                  ('viernes', 'Viernes'),
                                                                  ('sabado', 'Sabado'),
                                                                  ('domingo', 'Domingo'),])
    saldo_menbresia = fields.Char(compute='_compute_saldo_menbresia', string='Saldo Pendiente')
    facturas_ids = fields.One2many(comodel_name='account.invoice', inverse_name='partner_id', string='Menbresias Beneficiarios')
    
    
    
    @api.depends('facturas_ids')
    def _compute_saldo_menbresia(self):
        facturas=self.env['account.invoice'].search([('partner_id','=',self.id),('state','=','open')])
        saldo=0
        for f in facturas:
            saldo+=f.amount_total
        self.saldo_menbresia=saldo
    
