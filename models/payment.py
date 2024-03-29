from odoo import api, exceptions, fields, models, _
import base64
import xlrd
import io
from odoo.tools import pycompat
from datetime import datetime
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning


class Payment_wizard(models.TransientModel):
    _name = 'payment.wizard'
    
    # select_file = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='File Type')
    # option = fields.Selection([('create', 'Create'), ('skip', 'Skip ')], string='Operation')
    # state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted')], string='State')
    # payment_type = fields.Selection([('customer_py', 'Customer Payment'), ('supp_py', 'Supplier Payment')],string='Payment')
    data_file = fields.Binary(string="Archivo")
    journal_id = fields.Many2one('account.journal', string='Diario Pago',domain = "[('type','in',('cash','bank'))]")

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
            numero_documento=str(row[1]).replace('.0','')
            monto=str(row[5]).replace('.0','')
            fecha=str(row[3]).replace('.0','')
            
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
                fecha=datetime.strptime(fecha,"%d%m%Y").strftime("%Y-%m-%d")
                # fecha=fecha.strftime("%d-%m-%Y").strftime("%Y-%m-%d")
            except:
                raise exceptions.Warning(_('El formato de fecha debe ser ddmmyyyy.'))

            payment_vals = {
                'partner_type':'customer',
                'partner_id': partner_id,
                'payment_date': fecha,
                'journal_id':self.journal_id.id,
                'amount': monto,
                'communication': row[10],
                'payment_method_id': 1,
                'state': 'draft',
                'payment_type': 'inbound',
                }
#Busca la factura por fecha de vcto y si no existe no crea el pago                
            domain=[
                    ('state','=','open'),
                    ('partner_id','=',partner_id),
                    ('number','=',numero_documento)
                    ]
            facturas_abiertas=self.env['account.invoice'].search(domain,order="date_due",limit=1)

            if facturas_abiertas:
                payment_id = self.env['account.payment'].create(payment_vals)
                payment_id.post()


                payment_id.invoice_ids = [(4, facturas_abiertas.id)]
                facturas_abiertas.payment_ids=[(4, payment_id.id)] 
                facturas_abiertas.write({'state':'paid'})
                    # arma la sentencia SQL
                qry = """UPDATE account_invoice SET state = 'paid',
                                    reconciled=true,
                                    residual=0 ,
                                    residual_signed=0 ,
                                    residual_company_signed=0 
                                    WHERE id ={}"""

                qry=qry.format(facturas_abiertas.id)
                facturas_abiertas.env.cr.execute(qry)                            
            else:
                payment_id = self.env['account.payment'].create(payment_vals)                
        #Final del archivo envia mensaje al usuario indicando el status de los pagos
        warning = {
                    'title': 'Importación de pagos finalizada',
                    'message': """Los pagos fueron importados exitosamente. Los pagos a los cuales no
                                        se encontro la factura o si la factura existe pero esta pagada, estos
                                        pagos queron en estado borrador
                                    """,

                }
        return {'warning': warning}