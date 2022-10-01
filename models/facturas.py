from odoo import api, exceptions, fields, models, _
import base64
from odoo.exceptions import ValidationError
import xlrd
import io
from odoo.tools import pycompat
from datetime import datetime


class Payment_wizard(models.TransientModel):
    _name = 'invoice.wizard'
    
    # select_file = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='File Type')
    # option = fields.Selection([('create', 'Create'), ('skip', 'Skip ')], string='Operation')
    # state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted')], string='State')
    # payment_type = fields.Selection([('customer_py', 'Customer Payment'), ('supp_py', 'Supplier Payment')],string='Payment')
    data_file = fields.Binary(string="Archivo")
    journal_id = fields.Many2one('account.journal', string='Diario de Facturas',domain = "[('type','=','sale')]")
    product_id = fields.Many2one('product.product', string='Producto')

    @api.multi
    def Import_invoice(self):        
        try:
            file_datas = base64.decodestring(self.data_file)
            workbook = xlrd.open_workbook(file_contents=file_datas)
            sheet = workbook.sheet_by_index(0)
            data = [[sheet.cell_value(r, c) for c in range(sheet.ncols)] for r in range(sheet.nrows)]
            data.pop(0)
            file_data = data
        except:
            raise exceptions.Warning(_('Please select proper file type.'))

        Partner = self.env['res.partner']
        Journal = self.env['account.journal']

        contexto=self.env.context
        usuario=contexto['uid']

        for row in file_data:
            if not (row[0] or row[2] or row[3]):
                raise exceptions.Warning(_('Partner,Journal,Date values are required.'))
            rut=str(row[0]).replace('.0','')
            monto=str(row[3]).replace('.0','')
            fecha_emision=str(row[1]).replace('.0','')
            fecha_vcto=str(row[2]).replace('.0','')
            partner_id = Partner.search([('vat', '=ilike', rut)],limit=1)            
            if partner_id:
                partner_id=partner_id.id
            else:
                partner_id = Partner.search([('vat', '=ilike', rut),('active','=',False)],limit=1)            
                if partner_id:
                    partner_id=partner_id.id
                else:
                    raise ValidationError("Beneficiario con rut %s no existe!" % rut) 
            dia=fecha_emision[0:2]
            mes=fecha_emision[2:4]
            año=fecha_emision[4:8]     
            fecha_emision=dia+"-"+mes+"-"+año
            dia=fecha_vcto[0:2]
            mes=fecha_vcto[2:4]
            año=fecha_vcto[4:8]     
            fecha_vcto=dia+"-"+mes+"-"+año
            try:
                #date=datetime.strptime(fecha, '%d%m%Y').strftime('%d-%m-%y')
                date_emision=datetime.strptime(fecha_emision, '%d-%m-%Y').strftime('%Y-%m-%d')
                date_vcto=datetime.strptime(fecha_vcto, '%d-%m-%Y').strftime('%Y-%m-%d')
            except:
                raise exceptions.Warning(_('Date format must be dd-mm-yyyy.'))

            invoice_line=[]
            invoice_line.append(
                    (0, 0, {
                            "product_id": self.product_id.id,
                            "product_uom_qty":1,
                            "price_unit": monto,
                            "uom_id":self.product_id.product_tmpl_id.uom_id.id,
                            "name":self.product_id.product_tmpl_id.name,   
                            "account_id":self.product_id.categ_id.property_account_income_categ_id.id,
                            'invoice_line_tax_ids': [(6, 0, [x.id for x in self.product_id.taxes_id])],
                                            }))                                    


            values={
                    'date_invoice':date_emision,
                    'date_due':date_vcto,
                    'partner_id':partner_id,
                    'invoice_line_ids':invoice_line,
                    'amount_total':monto,
                    'amount_untaxed':monto,
                    'amount_tax':0,
                    'user_id':usuario
                    }            
            invoice_id = self.env['account.invoice'].create(values)
            invoice_id.action_invoice_open()
