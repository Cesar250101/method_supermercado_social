# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import ipdb

from odoo import fields, models
from odoo.exceptions import UserError

class StockWarnInsufficientQtyRepair(models.TransientModel):
    _name = 'method_supermercado_social.segundo_retiro'

    _description = 'Confirmación segundo retiro'

    asistencia_id = fields.Many2one('method_supermercado_social.asistencia', string='Asistencia')
    pin = fields.Char(string='PIN')

    def action_validate(self):
        for rec in self:
            employee_id = self.env['hr.employee'].search([('user_id','=',rec.env.user.id)])
            if not employee_id:
                raise UserError(f'El usuario {rec.env.user.name} no tiene un empleado asociado')
            if employee_id.pin != rec.pin:
                raise UserError('Pin incorrecto')

            rec.asistencia_id.show_warning = False
            rec.asistencia_id.action_validated = True