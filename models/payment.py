from odoo import api, exceptions, fields, models, _
import base64
from odoo.exceptions import ValidationError
import xlrd
import io
from odoo.tools import pycompat
from datetime import datetime


class Payment_wizard(models.TransientModel):
    _name = 'payment.wizard'
    
    # select_file = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='File Type')
    # option = fields.Selection([('create', 'Create'), ('skip', 'Skip ')], string='Operation')
    # state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted')], string='State')
    # payment_type = fields.Selection([('customer_py', 'Customer Payment'), ('supp_py', 'Supplier Payment')],string='Payment')
    data_file = fields.Binary(string="File")
    journal_id = fields.Many2one('account.journal', string='field_name',domain = "[('type','in',('cash','bank'))]")

    @api.multi
    def Import_payment(self):        
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

        for row in file_data:
            if not (row[0] or row[2] or row[3]):
                raise exceptions.Warning(_('Partner,Journal,Date values are required.'))
            rut=str(row[0]).replace('.0','')
            monto=str(row[1]).replace('.0','')
            fecha=str(row[4]).replace('.0','')
            partner_id = Partner.search([('vat', '=ilike', rut)],limit=1)            
            if partner_id:
                partner_id=partner_id.id
            else:
                partner_id = Partner.search([('vat', '=ilike', rut),('active','=',False)],limit=1)            
                if partner_id:
                    partner_id=partner_id.id
                else:
                    raise ValidationError("Beneficiario con rut %s no existe!" % rut)                

            try:
                date=datetime.strptime(fecha, '%d%m%YYYY').strftime('%d-%m-%y')
            except:
                raise exceptions.Warning(_('Date format must be dd-mm-yyyy.'))

            payment_vals = {
                'partner_type':'customer',
                'partner_id': partner_id,
                'payment_date': date,
                'journal_id':self.journal_id.id,
                'amount': monto,
                'communication': row[2],
                'payment_method_id': 1,
                'state': 'draft',
                'payment_type': 'inbound',
                }
            payment_id = self.env['account.payment'].create(payment_vals)
            payment_id.post()
