/*
    Copyright (C) 2016-Today: La Louve (<http://www.lalouve.net/>)
    @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
    License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
*/


odoo.define('method_supermercado_social.pos_campos', (require)=> {
    const { load_fields }=require('point_of_sale.models');
    load_fields('res.partner',['ultimo_retiro','saldo_menbresia']);
});
