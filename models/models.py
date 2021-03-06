# -*- coding: utf-8 -*-

from re import search
from odoo import models, fields, api
from odoo import exceptions 
import datetime
#import time 
#from time import gmtime, strftime
from datetime import datetime
from odoo.exceptions import ValidationError
from odoo.exceptions import ValidationError


class ModuleName(models.Model):
    _inherit = 'stock.scrap'

    motivo_merma = fields.Selection(string='Motivo Merma', selection=[('diferencia', 'Diferencia de inventario'), 
                                                                    ('vencido', 'Producto venció en bodega'),
                                                                    ('daño', 'Producto dañado'),
                                                                    ('ingreso', 'Error de ingreso'),
                                                                    ('sala', 'Merma en sala')],
                                                            required=True)
    

class OdenesPos(models.Model):
    _inherit = 'pos.order'

    @api.constrains('partner_id')
    def _check_partner_id(self):
        fecha_actual=datetime.today()
        fecha_desde=fecha_actual.strftime("%d/%m/%Y")
        fecha_hasta=fecha_desde+" 23:59:59"
        domain=[
            ('partner_id','=',self.partner_id.id),
            ('date_order','>=',fecha_desde),
            ('date_order','<=',fecha_hasta),
            ('id','!=',self.id),
        ]
    


class ModuleName(models.Model):
    _inherit = 'stock.picking'


    @api.one
    def valida_entrega_uno(self):
        move=self.env['stock.move'].search([('picking_id','=',self.id)])
        for m in move:
            move_line=self.env['stock.move.line'].search([('move_id','=',m.id)])
            if not move_line:
                domain = [
                            ("product_id", "=", m.product_id.id),
                            ("quantity", ">", 0),
                            ('location_id','=',self.location_id.id)
                        ]
                lote=self.env['stock.quant'].search(domain,order="in_date",limit=1)                
                vals={
                        'picking_id':self.id,
                        'move_id':m.id,
                        'product_id':m.product_id.id,
                        'product_uom_id':m.product_uom.id,
                        #'product_uom_qty':m.product_uom_qty,
                        #'product_qty':m.product_uom_qty,
                        'qty_done':m.product_uom_qty,
                        'location_id':m.location_id.id,
                        'location_dest_id':m.location_dest_id.id,
                        'lot_id':lote.lot_id.id,
                    }
                move_line.sudo().create(vals)
                move_line=self.env['stock.move.line'].search([('move_id','=',m.id)])
        self.button_validate()


    @api.model
    def valida_entrega(self):
        pendientes=self.search([("state","in",['assigned','confirmed'])],limit=100)
        for p in pendientes:
            move=self.env['stock.move'].search([('picking_id','=',p.id)])
            for m in move:                
                values={
                            'reserved_availability':m.product_uom_qty
                        }
                m.sudo().write(values)
                move_line=self.env['stock.move.line'].search([('move_id','=',m.id)])
                domain = [
                                ("product_id", "=", m.product_id.id),
                                ("quantity", ">", 0),
                                ('location_id','=',p.location_id.id)
                            ]                
                if not move_line:
                    domain = [
                                ("product_id", "=", m.product_id.id),
                                ("quantity", ">", 0),
                                ('location_id','=',p.location_id.id)
                            ]
                    lote=self.env['stock.quant'].search(domain,order="in_date",limit=1)                       
                    vals={
                            'picking_id':p.id,
                            'move_id':m.id,
                            'product_id':m.product_id.id,
                            'product_uom_id':m.product_uom.id,
                            #'product_uom_qty':m.product_uom_qty,
                            #'product_qty':m.product_uom_qty,
                            'qty_done':m.product_uom_qty,
                            'location_id':m.location_id.id,
                            'location_dest_id':m.location_dest_id.id,
                            'lot_id':lote.lot_id.id,
                        }
                    move_line.sudo().create(vals)
                    move_line=self.env['stock.move.line'].search([('move_id','=',m.id)])                    
                else:
                    lote=self.env['stock.quant'].search(domain,order="in_date",limit=1)                       
                    vals={
                        'qty_done':m.product_uom_qty,
                        'lot_id':lote.lot_id.id
                    }
                    move_line.sudo().write(vals)
            p.button_validate()


class Clientes(models.Model):
    _inherit = 'res.partner'

    codigo_qr = fields.Char(string='Código QR')
    grupo_familiar = fields.Integer(string='Tamaño grupo familiar',help='Número de integrantes del grupo familiar')
    hora_retiro = fields.Char(string='Hora de Retiro')
    dia_retiro = fields.Selection(string='Día Retiro', selection=[('lunes', 'Lunes'), 
                                                                  ('martes', 'Martes'),
                                                                  ('miercoles', 'Miercoles'),
                                                                  ('jueves', 'Jueves'),
                                                                  ('viernes', 'Viernes'),
                                                                  ('sabado', 'Sabado'),
                                                                  ('domingo', 'Domingo'),])
    saldo_menbresia = fields.Integer(compute='_compute_saldo_menbresia', string='Saldo Pendiente')
    facturas_ids = fields.One2many(comodel_name='account.invoice', inverse_name='partner_id', string='Menbresias Beneficiarios')
    asistencia_ids = fields.One2many(comodel_name='method_supermercado_social.asistencia', inverse_name='partner_id', string='Retiros')
    ultimo_retiro = fields.Datetime(string='Ultimo Retiro',compute="_compute_ultimo_retiro")

    

    @api.depends('asistencia_ids')
    def _compute_ultimo_retiro(self):
        for i in self:
            partner_id=i.id
            try: 
                retiro_last = self.env['method_supermercado_social.asistencia'].search([('partner_id','=',partner_id)])[-1].create_date
            except: 
                retiro_last=False
            i.ultimo_retiro=retiro_last
            
    
    @api.one
    @api.depends('facturas_ids')
    def _compute_saldo_menbresia(self):    
        facturas=self.env['account.invoice'].search([('partner_id','=',self.id),('state','=','open')])
        saldo=0
        for f in facturas:
            saldo+=f.amount_total
        self.saldo_menbresia=saldo
    


class Registro(models.Model):
    _name = 'method_supermercado_social.asistencia'
    _description = 'Registro de beneficiarios'

    name = fields.Char(string='Name')
    codigo_qr = fields.Char(string='Código QR')    
    partner_id = fields.Many2one(comodel_name='res.partner', string='Beneficiario',default="")
    grupo_familiar = fields.Integer(string='Tamaño grupo familiar',help='Número de integrantes del grupo familiar')
    hora_retiro = fields.Char(string='Hora de Retiro')
    dia_retiro = fields.Char(string='Día Retiro')
    saldo_menbresia = fields.Integer(string='Saldo Pendiente')
    buscar_rut = fields.Boolean(string='Buscar por RUT')
    rut = fields.Char(string='Rut Beneficiario')
    ultimo_retiro = fields.Datetime(string='Ultimo Retiro',related="partner_id.ultimo_retiro")
    dif_nro_semana = fields.Integer(string='N° Semana')


    @api.onchange('partner_id')
    def _check_create_date(self):
        fecha_ultimo=self.search([('partner_id','=',self.partner_id.id)],order='create_date desc',limit=1).create_date
        if fecha_ultimo:
            fecha_ultimo=fecha_ultimo.date()
            fecha_actual_date=datetime.now().date()
            if fecha_ultimo>=fecha_actual_date:
                raise ValidationError("Beneficiario ya esta registrado como asisten el día de hoy!")    

    @api.depends('ultimo_retiro')
    def _compute_nro_semana(self):
        nrosemana=datetime.date(self.create_date).strftime("%V")
        print(nrosemana)

    

    @api.onchange('codigo_qr','rut')
    def _onchange_codigo_qr(self):
        partner=False
        if self.buscar_rut==False and self.codigo_qr:
            partner=self.env['res.partner'].search([('codigo_qr','=',self.codigo_qr)],limit=1)
        elif self.buscar_rut==True and self.rut:
            rut=self.rut.replace('-','')
            rut=rut.replace('.','')
            partner=self.env['res.partner'].search([('vat','=',rut)],limit=1)
        if partner:
            self.partner_id=partner.id
            self.grupo_familiar=partner.grupo_familiar
            self.hora_retiro=partner.hora_retiro
            self.dia_retiro=partner.dia_retiro
            self.saldo_menbresia=partner.saldo_menbresia
            self.codigo_qr=partner.codigo_qr
            self.ultimo_retiro=partner.ultimo_retiro
            fecha_actual=datetime.today()            
            nrosemana_actual=datetime.date(fecha_actual).isocalendar()[1]            
            if self.ultimo_retiro==False:
                nrosemana_ultima=0
            else:    
                nrosemana_ultima=datetime.date(self.partner_id.ultimo_retiro).isocalendar()[1]                            
            dif_nro_semana=nrosemana_actual-nrosemana_ultima
            #print(dif_nro_semana)
            self.dif_nro_semana=nrosemana_actual-nrosemana_ultima
            # if self.codigo_qr:
            #     vals={
            #          'codigo_qr':self.codigo_qr
            #      }
            #     partner.sudo().write(vals)

            

        else:
            self.partner_id=""
            self.grupo_familiar=""
            self.hora_retiro=""
            self.dia_retiro=""
            self.saldo_menbresia=""
            self.codigo_qr=""
            self.ultimo_retiro=""
            self.dif_nro_semana=""
            if self.codigo_qr or self.rut:
                raise exceptions.UserError('Código QR o RUT no asociado al cliente, seleccione al beneficiario de forma manual y grabe el registro')

class Desecho(models.Model):
    _inherit = 'stock.scrap'

    motivo_desecho = fields.Text('Observación ')
    