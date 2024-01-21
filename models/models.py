# -*- coding: utf-8 -*-

from ast import Continue
from distutils.log import info
from re import search

from aiohttp import request

# import ipdb

from odoo import models, fields, api, _
from odoo import exceptions
import datetime
from datetime import date
# import time
# from time import gmtime, strftime
from datetime import datetime
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning


class Pagos(models.Model):
    _inherit = 'account.payment'
    _description = 'Pagos de Facturas'

    fecha_vcto = fields.Date('Fecha Vcto.')

    @api.model
    def calzar_pagos(self):
        pagos_sin_calzar = self.env['account.payment'].search([('invoice_ids', '=', False)])
        for p in pagos_sin_calzar:
            domain = [('state', '=', 'open'), ('partner_id', '=', p.partner_id.id)]
            facturas_abiertas = self.env['account.invoice'].search(domain, order="date_due", limit=1)
            if facturas_abiertas:
                p.invoice_ids = [(4, facturas_abiertas.id)]
                facturas_abiertas.payment_ids = [(4, p.id)]
                facturas_abiertas.write({'state': 'paid'})
                # arma la sentencia SQL
                qry = """UPDATE account_invoice SET state = 'paid',
                                reconciled=true,
                                residual=0 ,
                                residual_signed=0 ,
                                residual_company_signed=0 
                                WHERE id ={}"""

                qry = qry.format(facturas_abiertas.id)
                facturas_abiertas.env.cr.execute(qry)

class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    # motivo_merma = fields.Selection(string='Motivo Merma', selection=[('diferencia', 'Diferencia de inventario'), 
    #                                                                 ('vencido', 'Producto venció en bodega'),
    #                                                                 ('daño', 'Producto dañado'),
    #                                                                 ('ingreso', 'Error de ingreso'),
    #                                                                 ('sala', 'Merma en sala')],
    #                                                         required=True)
    motivo_merma_id = fields.Many2one(comodel_name='method_supermercado_social.motivo_merma', string='Motivo Merma',required=True)

class MotivoMerma(models.Model):
    _name = 'method_supermercado_social.motivo_merma'
    _description = 'Motivos de merma para poder clasificar los desechos'
    
    name = fields.Char(string='Nombre')
    active = fields.Boolean(string='Activo',default=True)


class OdenesPos(models.Model):
    _inherit = 'pos.order'

    @api.constrains('partner_id')
    def _check_partner_id(self):
        fecha_actual = datetime.today()
        fecha_desde = fecha_actual.strftime("%d/%m/%Y")
        fecha_hasta = fecha_desde + " 23:59:59"
        domain = [
            ('partner_id', '=', self.partner_id.id),
            ('date_order', '>=', fecha_desde),
            ('date_order', '<=', fecha_hasta),
            ('id', '!=', self.id),
        ]


class ModuleName(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def eliminar_reservas(self):
        query = "delete from stock_move_line sml where state ='assigned'"
        self.env.cr.execute(query)

    @api.one
    def valida_entrega_uno(self):
        move = self.env['stock.move'].search([('picking_id', '=', self.id)])
        for m in move:
            move_line = self.env['stock.move.line'].search([('move_id', '=', m.id)])
            if not move_line:
                domain = [
                    ("product_id", "=", m.product_id.id),
                    ("quantity", ">", 0),
                    ('location_id', '=', self.location_id.id)
                ]
                lote = self.env['stock.quant'].search(domain, order="in_date", limit=1)
                vals = {
                    'picking_id': self.id,
                    'move_id': m.id,
                    'product_id': m.product_id.id,
                    'product_uom_id': m.product_uom.id,
                    # 'product_uom_qty':m.product_uom_qty,
                    # 'product_qty':m.product_uom_qty,
                    'qty_done': m.product_uom_qty,
                    'location_id': m.location_id.id,
                    'location_dest_id': m.location_dest_id.id,
                    'lot_id': lote.lot_id.id,
                }
                move_line.sudo().create(vals)
                move_line = self.env['stock.move.line'].search([('move_id', '=', m.id)])
        self.button_validate()


class Clientes(models.Model):
    _inherit = 'res.partner'

    codigo_qr = fields.Char(string='Código QR')
    grupo_familiar = fields.Integer(string='Tamaño grupo familiar', help='Número de integrantes del grupo familiar')
    hora_retiro = fields.Char(string='Hora de Retiro')
    dia_retiro = fields.Selection(string='Día Retiro', selection=[('lunes', 'Lunes'),
                                                                  ('martes', 'Martes'),
                                                                  ('miercoles', 'Miercoles'),
                                                                  ('jueves', 'Jueves'),
                                                                  ('viernes', 'Viernes'),
                                                                  ('sabado', 'Sabado'),
                                                                  ('domingo', 'Domingo'), ])
    saldo_menbresia = fields.Integer(compute='_compute_saldo_menbresia', string='Saldo Pendiente',store=True)
    membresias_vencidas = fields.Integer(compute='_compute_saldo_menbresia', string='Membresias Vencidas')
    membresias_por_vencidas = fields.Integer(compute='_compute_saldo_menbresia', string='Membresias por Vencidas')
    facturas_ids = fields.One2many(comodel_name='account.invoice', inverse_name='partner_id',
                                   string='Menbresias Beneficiarios')
    asistencia_ids = fields.One2many(comodel_name='method_supermercado_social.asistencia', inverse_name='partner_id',
                                     string='Retiros')
    ultimo_retiro = fields.Datetime(string='Ultimo Retiro', compute="_compute_ultimo_retiro",store=True)
    state_2_retiro = fields.Selection(
        [
            ("no_autorizado", "No Autorizado"),
            ("autorizado", "Autorizado"),
        ],
        string="Autoriza Retiro?",
        help="Indica si se autorizo el segundo retiro en la misma semana",
        copy=False,
        default='no_autorizado'
    )      
    # motivo_desactivacion = fields.Char('Motivo Desactivación')

    @api.model
    def eliminar_autoriacion_beneficiario(self):
        sql="""update res_partner rp
        set state_2_retiro ='no_autorizado'
        where coalesce(state_2_retiro,'') ='autorizado'  """

        self.env.cr.execute(sql)
        


    @api.one
    @api.depends('facturas_ids', 'facturas_ids.state')
    def _compute_saldo_menbresia(self):
        facturas = self.env['account.invoice'].search([('partner_id', '=', self.id), ('state', '=', 'open')])
        saldo = 0
        for f in facturas:
            saldo += f.amount_total
        self.saldo_menbresia = saldo

    @api.depends('asistencia_ids')
    def _compute_ultimo_retiro(self):
        for i in self:
            partner_id = i.id
            try:
                retiro_last = \
                self.env['method_supermercado_social.asistencia'].search([('partner_id', '=', partner_id)])[
                    -1].create_date
            except:
                retiro_last = False
            i.ultimo_retiro = retiro_last


class Registro(models.Model):
    _name = 'method_supermercado_social.asistencia'
    _description = 'Registro de beneficiarios'



    name = fields.Char(string='Name')
    codigo_qr = fields.Char(string='Código QR')
    partner_id = fields.Many2one(comodel_name='res.partner', string='Beneficiario', default="")
    grupo_familiar = fields.Integer(string='Tamaño grupo familiar', help='Número de integrantes del grupo familiar')
    hora_retiro = fields.Char(string='Hora de Retiro')
    dia_retiro = fields.Char(string='Día Retiro')
    saldo_menbresia = fields.Integer(string='Saldo Pendiente')
    buscar_rut = fields.Boolean(string='Buscar por RUT')
    rut = fields.Char(string='Rut Beneficiario')
    ultimo_retiro = fields.Datetime(string='Ultimo Retiro', related="partner_id.ultimo_retiro")
    # motivo_desactivacion = fields.Char('Motivo Desactivación',related='partner_id.motivo_desactivacion')
    dif_nro_semana = fields.Integer(string='N° Semana Último Retiro')
    show_warning = fields.Boolean()
    action_validated = fields.Boolean()
    state = fields.Selection(
        [
            ("no_autorizado", "No Autorizado"),
            ("autorizado", "Autorizado"),
        ],
        string="Estado",
        help="Indica si se autorizo el segundo retiro en la misma semana",
        copy=False,
        default='no_autorizado'
    )    

    @api.one
    def autorizar_2_retiro(self):
        grupo_autorizacion=self.env.user.has_group('point_of_sale.group_pos_manager')         
        if grupo_autorizacion:
            self.state='autorizado'
            self.partner_id.state_2_retiro='autorizado'
        else:
            raise exceptions.UserError('Usuario no tiene permisos para autorizar un 2° retiro!')



    @api.model
    def create(self, vals):
        res = super(Registro, self).create(vals)        
        grupo_autorizacion=self.env.user.has_group('point_of_sale.group_pos_manager') 
        if res.dif_nro_semana!=0 or grupo_autorizacion:
            res.state='autorizado'
        else:
            res.state='no_autorizado'
        return res

        
    @api.onchange('partner_id')
    def _check_create_date(self):
        fecha_ultimo = self.search([('partner_id', '=', self.partner_id.id)], order='create_date desc',limit=1).create_date
        if fecha_ultimo:
            fecha_ultimo = fecha_ultimo.date()
            fecha_actual_date = datetime.now().date()
            if self.dif_nro_semana==0:
                self.show_warning = True
                warning = {
                    'title': 'Segundo retiro en 7 día',
                    'message': "Beneficiario realizó un retiro el {}".format(self.ultimo_retiro),

                }
                return {'warning': warning}
                # raise ValidationError()

    @api.multi
    def action_open_wizard(self):
        action_wizard_view = self.env.ref('method_supermercado_social.action_supermercado_social_segundo_retiro').read()[0]
        action_wizard_view['views'] = [(self.env.ref('method_supermercado_social.segundo_retiro_form_view').id, 'form')]
        action_wizard_obj = self.env['method_supermercado_social.segundo_retiro']
        values = {
            'asistencia_id': self.id,
        }
        action_wizard = action_wizard_obj.create(values)
        action_wizard_view['res_id'] = action_wizard.id
        return action_wizard_view

    @api.depends('ultimo_retiro')
    def _compute_nro_semana(self):
        nrosemana = datetime.date(self.create_date).strftime("%V")
        print(nrosemana)

    @api.onchange('codigo_qr', 'rut')
    def _onchange_codigo_qr(self):
        partner = False
        if self.buscar_rut == False and self.codigo_qr:
            partner = self.env['res.partner'].search([('codigo_qr', '=', self.codigo_qr)], limit=1)
        elif self.buscar_rut == True and self.rut:
            rut = self.rut.replace('-', '')
            rut = rut.replace('.', '')
            partner = self.env['res.partner'].search([('vat', '=', rut)], limit=1)
        if partner:
            self.partner_id = partner.id
            self.grupo_familiar = partner.grupo_familiar
            self.hora_retiro = partner.hora_retiro
            self.dia_retiro = partner.dia_retiro
            self.saldo_menbresia = partner.saldo_menbresia
            self.codigo_qr = partner.codigo_qr
            self.ultimo_retiro = partner.ultimo_retiro
            fecha_actual = datetime.today()
            nrosemana_actual = datetime.date(fecha_actual).isocalendar()[1]
            if self.ultimo_retiro == False:
                nrosemana_ultima = 0
            else:
                nrosemana_ultima = datetime.date(self.partner_id.ultimo_retiro).isocalendar()[1]
            dif_nro_semana = nrosemana_actual - nrosemana_ultima
            # print(dif_nro_semana)
            self.dif_nro_semana = nrosemana_actual - nrosemana_ultima
            # if self.codigo_qr:
            #     vals={
            #          'codigo_qr':self.codigo_qr
            #      }
            #     partner.sudo().write(vals)
            fecha_actual = date.today()
            domain = [('state', '=', 'open'),
                      # ('date_due','<=',fecha_actual),
                      ('partner_id', '=', partner.id)
                      ]
            saldo_vencido = self.env['account.invoice'].search(domain)
            saldo = 0
            saldo_por_vencer = 0
            msg = ""
            if saldo_vencido:
                for s in saldo_vencido:
                    if s.date_due <= date.today():
                        saldo += s.amount_total
                    else:
                        saldo_por_vencer += s.amount_total
                if saldo != 0:
                    msg = "El beneficiario {} tiene Membresía Vencida!".format(partner.name)
                if saldo_por_vencer != 0:
                    msg += " El beneficiario {} tiene Membresía pendientes!".format(partner.name)
                return {'warning': {'title': "Deuda vencida", 'message': msg}}






        else:
            self.partner_id = ""
            self.grupo_familiar = ""
            self.hora_retiro = ""
            self.dia_retiro = ""
            self.saldo_menbresia = ""
            self.codigo_qr = ""
            self.ultimo_retiro = ""
            self.dif_nro_semana = ""
            if self.codigo_qr or self.rut:
                raise exceptions.UserError(
                    'Código QR o RUT no asociado al cliente, seleccione al beneficiario de forma manual y grabe el registro')



