// static/src/js/pos_cliente_validation.js
odoo.define('method_supermercado_social.pos_cliente_validation', function (require) {
    "use strict";
    
    var screens = require('point_of_sale.screens');
    var core = require('web.core');
    var QWeb = core.qweb;
    var _t = core._t;
    var rpc = require('web.rpc');    

    var models = require('point_of_sale.models');
    const { load_fields }=require('point_of_sale.models');
    load_fields('res.partner',['state_2_retiro']);

    screens.PaymentScreenWidget.include({

        order_is_valid: function(force_validation) {
            var self = this;
            var res = this._super(force_validation);
            var order = self.pos.get_order();

            var client = order.get_client();
            console.log(client)

            if (client.state_2_retiro==='no_autorizado'){
                        this.gui.show_popup('error',{
                            'title': 'Falta Autorización',
                            'body':  'El Beneficiario seleccionado no ha sido autorizado en el registro de entrada!',
                        });
                        return false;
            }
            else{
                return true;
            }
            
        }
    });
});