/*
    Copyright (C) 2016-Today: La Louve (<http://www.lalouve.net/>)
    @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
    License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
*/


odoo.define('method_supermercado_social.pos_campos', (require)=> {
    // var _super_posmodel = models.PosModel.prototype;
    // models.PosModel = models.PosModel.extend({
    //     initialize: function(session,attributes)
    //     {
    //         var contact_model = _.find(this.models,function(model)
    //         {
    //             return model.model === 'res.partner';
    //         });
    //         contact_model.fields.push('ultimo_retiro');
    //         return _super_posmodel.initialize.call(this,session,attributes);
    //     },
    // });
    const { load_fields }=require('point_of_sale.models');
    load_fields('res.partner',['ultimo_retiro']);


});
