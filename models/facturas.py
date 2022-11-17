from odoo import api, exceptions, fields, models, _
import base64
from odoo.exceptions import ValidationError
import xlrd
import io
from odoo.tools import pycompat
from datetime import datetime
from odoo.tools.safe_eval import safe_eval

class Payment_wizard(models.TransientModel):
    _name = 'invoice.wizard'
    
    # select_file = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='File Type')
    # option = fields.Selection([('create', 'Create'), ('skip', 'Skip ')], string='Operation')
    # state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted')], string='State')
    # payment_type = fields.Selection([('customer_py', 'Customer Payment'), ('supp_py', 'Supplier Payment')],string='Payment')
    document_type = fields.Selection([('facturas', 'Facturas'), ('nc', 'Notas de Crédito')],string='Tipo Documento')
    data_file = fields.Binary(string="Archivo")
    journal_id = fields.Many2one('account.journal', string='Diario de Facturas',domain = "[('type','=','sale')]")
    product_id = fields.Many2one('product.product', string='Producto')
    validar_factura = fields.Boolean('Validar Facturas?')

    @api.multi
    def Import_invoice(self):     
        if self.document_type=="facturas":   
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
                    raise exceptions.Warning(_('Date format must be ddMMyyyy.'))

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
                if self.validar_factura:
                    invoice_id.action_invoice_open()
        else:
            new_factura=self.env['account.invoice']
            try:
                file_datas = base64.decodestring(self.data_file)
                workbook = xlrd.open_workbook(file_contents=file_datas)
                sheet = workbook.sheet_by_index(0)
                data = [[sheet.cell_value(r, c) for c in range(sheet.ncols)] for r in range(sheet.nrows)]
                data.pop(0)
                file_data = data
            except:
                raise exceptions.Warning(_('Please select proper file type.'))
            for row in file_data:
                fecha=row[1]
                fecha_emision=str(row[1])
                dia=fecha_emision[0:2]
                mes=fecha_emision[3:5]
                año=fecha_emision[6:10]     
                fecha_emision=año+"-"+mes+"-"+dia                
                nro_factura=row[0]
                factura=self.env['account.invoice'].search([('number','=',nro_factura)],limit=1)
                if factura:
                    factura_line=[]  
                    for i in factura.invoice_line_ids:
                        factura_line.append(
                                            (0, 0, {
                                            "product_id": i.product_id.id,
                                            "product_uom_qty":i.quantity,
                                            "price_unit": i.price_unit,
                                            "discount":i.discount,
                                            "product_uom":i.product_id.product_tmpl_id.uom_id.id,
                                            "name":i.product_id.product_tmpl_id.name,   
                                            "account_id":i.product_id.product_tmpl_id.categ_id.property_account_expense_categ_id.id
                                            }))                                       
                    vals={
                        'type': 'out_refund',
                        'refund_invoice_id':factura.id,
                        'state':'draft',
                        'partner_id':factura.partner_id.id,
                        'company_id':factura.company_id.id,
                        'date_invoice':fecha_emision,
                        'date_due':fecha_emision,
                        'date':fecha_emision,
                        'amount_untaxed_signed':(factura.amount_untaxed_signed)*-1,
                        'amount_total_signed':(factura.amount_total_signed)*-1,
                        'amount_total_company_signed':(factura.amount_total_company_signed)*-1,
                        'invoice_line_ids':factura_line
                    }
                    nota_credito=new_factura.create(vals)
                    # nota_credito = factura.copy(default={'type': 'out_refund',
                    # 'refund_invoice_id':factura.id,
                    # 'state':'draft',
                    # 'company_id':factura.company_id.id,
                    # 'date_invoice':fecha_emision,
                    # 'date_due':fecha_emision,
                    # 'date':fecha_emision,
                    # 'amount_untaxed_signed':(factura.amount_untaxed_signed)*-1,
                    # 'amount_total_signed':(factura.amount_total_signed)*-1,
                    # 'amount_total_company_signed':(factura.amount_total_company_signed)*-1,
                    # })
                    conciliar=self.conciliar_nc(mode='cancel',factura_id=factura,nota_credito=nota_credito)
                    print(conciliar)

    @api.multi
    def conciliar_nc(self, mode='refund',factura_id=False,nota_credito=False):
        inv_obj = self.env['account.invoice']
        inv_tax_obj = self.env['account.invoice.tax']
        inv_line_obj = self.env['account.invoice.line']
        context = dict(self._context or {})
        xml_id = False
        invoice_refund=self.env['account.invoice.refund']
        for form in self:
            created_inv = []
            date = False
            description = False
            refund = nota_credito
            created_inv.append(refund.id)
            if mode in ('cancel', 'modify'):
                movelines = factura_id.move_id.line_ids
                to_reconcile_ids = {}
                to_reconcile_lines = self.env['account.move.line']
                for line in movelines:
                    if line.account_id.id == factura_id.account_id.id:
                        to_reconcile_lines += line
                        to_reconcile_ids.setdefault(line.account_id.id, []).append(line.id)
                    if line.reconciled:
                        line.remove_move_reconcile()
                refund.action_invoice_open()
                for tmpline in refund.move_id.line_ids:
                    if tmpline.account_id.id == factura_id.account_id.id:
                        to_reconcile_lines += tmpline
                to_reconcile_lines.filtered(lambda l: l.reconciled == False).reconcile()
                xml_id = factura_id.type == 'out_invoice' and 'action_invoice_out_refund' or \
                         factura_id.type == 'out_refund' and 'action_invoice_tree1' or \
                         factura_id.type == 'in_invoice' and 'action_invoice_in_refund' or \
                         factura_id.type == 'in_refund' and 'action_invoice_tree2'
        if xml_id:
            result = self.env.ref('account.%s' % (xml_id)).read()[0]
            if mode == 'modify':
                # When refund method is `modify` then it will directly open the new draft bill/invoice in form view
                if inv_refund.type == 'in_invoice':
                    view_ref = self.env.ref('account.invoice_supplier_form')
                else:
                    view_ref = self.env.ref('account.invoice_form')
                form_view = [(view_ref.id, 'form')]
                if 'views' in result:
                    result['views'] = form_view + [(state,view) for state,view in result['views'] if view != 'form']
                else:
                    result['views'] = form_view
                result['res_id'] = inv_refund.id
            else:
                invoice_domain = safe_eval(result['domain'])
                invoice_domain.append(('id', 'in', created_inv))
                result['domain'] = invoice_domain
            return result
        return True
