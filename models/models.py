# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo import exceptions 

class Clientes(models.Model):
    _inherit = 'res.partner'

    codigo_qr = fields.Char(string='Código QR')
    grupo_familiar = fields.Integer(string='Tamaño grupo familiar',help='Número de integrantes del grupo familiar')
    hora_retiro = fields.Float(string='Hora de Retiro')
    dia_retiro = fields.Selection(string='Día Retiro', selection=[('lunes', 'Lunes'), 
                                                                  ('martes', 'Martes'),
                                                                  ('miercoles', 'Miercoles'),
                                                                  ('jueves', 'Jueves'),
                                                                  ('viernes', 'Viernes'),
                                                                  ('sabado', 'Sabado'),
                                                                  ('domingo', 'Domingo'),])
    saldo_menbresia = fields.Integer(compute='_compute_saldo_menbresia', string='Saldo Pendiente')
    facturas_ids = fields.One2many(comodel_name='account.invoice', inverse_name='partner_id', string='Menbresias Beneficiarios')
    
    
    
    @api.one
    @api.depends('facturas_ids')
    def _compute_saldo_menbresia(self):    
        facturas=self.env['account.invoice'].search([('partner_id','=',self.id),('state','=','open')])
        saldo=0
        for f in facturas:
            saldo+=f.amount_total
        self.saldo_menbresia=saldo
    


class ModuleName(models.Model):
    _name = 'method_supermercado_social.asistencia'
    _description = 'Registro de beneficiarios'

    name = fields.Char(string='Name')
    codigo_qr = fields.Char(string='Código QR')    
    partner_id = fields.Many2one(comodel_name='res.partner', string='Beneficiario',required=True)
    grupo_familiar = fields.Integer(string='Tamaño grupo familiar',help='Número de integrantes del grupo familiar')
    hora_retiro = fields.Float(string='Hora de Retiro')
    dia_retiro = fields.Char(string='Día Retiro')
    saldo_menbresia = fields.Integer(string='Saldo Pendiente')


    @api.onchange('codigo_qr')
    def _onchange_codigo_qr(self):
        partner=self.env['res.partner'].search([('codigo_qr','=',self.codigo_qr)],limit=1)
        if partner:
            self.partner_id=partner.id
            self.grupo_familiar=partner.grupo_familiar
            self.hora_retiro=partner.hora_retiro
            self.dia_retiro=partner.dia_retiro
            self.saldo_menbresia=partner.saldo_menbresia
            self.codigo_qr=partner.codigo_qr
        else:
            raise exceptions.UserError('Código QR no asociado al cliente, seleccione al beneficiario de forma manual y grabe el registro')
            
    

    
    

