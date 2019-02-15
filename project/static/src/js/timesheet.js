odoo.define('project.project_chart', function (require) {
"use strict";

var core = require('web.core');
var data = require('web.data');
var form_common = require('web.form_common');
var formats = require('web.formats');
var Model = require('web.DataModel');
var time = require('web.time');
var utils = require('web.utils');
var session = require('web.session');

var QWeb = core.qweb;
var _t = core._t;

//document.write('<script src="https://www.gstatic.com/charts/loader.js"></script>')
var ProjectChart = form_common.FormWidget.extend(form_common.ReinitializeWidgetMixin, {
    template: 'project.ProjectChart',
    init: function() {
        this._super.apply(this, arguments);
	var self = this;

	google.charts.load('current',{'packages':['timeline']});
	google.charts.setOnLoadCallback(this.drawChart);
    },
    drawChart: function(){
        session.rpc('/web/dataset/search_read',{
	   model : 'project.timeline',
	}).then(function(id){
          var container = document.getElementById('chart_div');
	  var chart = new google.visualization.Timeline(container);
          var data = new google.visualization.DataTable();

	  data.addColumn({type:'string',id: 'Role'});
	  data.addColumn({type:'string',id: 'Name'});
	  data.addColumn({type:'date',id: 'Start'});
	  data.addColumn({type:'date',id: 'End'});

          $.each(id.records, function(index, item){
	     if(item.name == false){
	       return
	     }
	     data.addRow(
	       [item.project[1], item.name, new Date(item.date_from), new Date(item.date_to)]
	     );
          });
	  var options = {
	    timeline: {groupByRowLabel: true},
	    vAxes: {},
	    height: 500,
	  };

	  chart.draw(data, options);
	  google.visualization.events.addListener(chart, 'select', function(e){
	    var selection = chart.getSelection();
	    console.log(selection)
	  });
        });
    }
});

core.form_custom_registry.add('project_chart', ProjectChart);

});
