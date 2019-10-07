odoo.define('gvm.gvmsign', function (require) {
"use strict";

var core = require('web.core');
var data = require('web.data');
var form_common = require('web.form_common');
var formats = require('web.formats');
var Dialog = require('web.Dialog');
var Model = require('web.DataModel');
var time = require('web.time');
var utils = require('web.utils');
var KanbanView = require('web_kanban.KanbanView');

var QWeb = core.qweb;
var _t = core._t;

var gvmSignDashboard = KanbanView.extend({
    fetch_data: function() {
        // Overwrite this function with useful data
        return $.when();
    },
    render: function() {
        var super_render = this._super;
        var self = this;

        return this.fetch_data().then(function(result){

            var sales_dashboard = QWeb.render('gvm.Dashboard', {
                widget: self,
                values: result,
            });
            super_render.call(self);
            $(sales_dashboard).prependTo(self.$el);
        });
    },
})
core.view_registry.add('gvm_sign_dashboard', gvmSignDashboard);

return gvmSignDashboard;

});
