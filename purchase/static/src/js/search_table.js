odoo.define('purchase.search_Table', function (require) {
"use strict";

var core = require('web.core');
var data = require('web.data');
var form_common = require('web.form_common');
var formats = require('web.formats');
var Model = require('web.DataModel');
var time = require('web.time');
var utils = require('web.utils');
var session = require('web.session');
var form_view = require('web.FormView');

var QWeb = core.qweb;
var _t = core._t;

var Product = new Model('gvm.product');
var SearchTable = form_common.FormWidget.extend(form_common.ReinitializeWidgetMixin, {
    template: 'purchase.Search_Table',
    events:{ 
        'click #product_search': 'loading',
        'change #gvm_search_product': 'update_project',
        'change #gvm_search_product_part': 'update_part',
	'click #gvm_save': 'save',
	'click #gvm_purchase_order': 'purchase',
    },
    init: function() {
        this._super.apply(this, arguments);
	var self = this;
        this.data = [];
	this.data_id = [];
	this.update_content = [];
	this.search_filter = [];
	this.Numtmp_row = [];
	this.Numtmp_col = [];
	this.original_data = [];
	this.colHeaders = ['O','번호','도번 및 규격','품명','재질','원수','비고','상태','발주서번호'];
        var Project = new Model('project.project');
        //Project.query(['name']).filter([['code','!=',false],['is_finish','=',false],['project_rate','=','1']]).all().then(function(id){
        Project.query(['name']).filter([['is_finish','=',false]]).all().then(function(id){
          $.each(id, function(index, item){
            $('#gvm_search_product').append('<option id="'+index+'" value="'+item.id+'">'+item.name+'</option>');
	  })});
	//button create
	//button hide
	setTimeout(function(){
	  $('.o_form_button_save').hide();
	  $('.o_form_button_cancel').hide();
	},100);

    },
    update_project: function(){
    	var self = this;
	var project_selected = $('#gvm_search_product option:selected').text();
        var Part = new Model('project.issue');
	this.search_filter = [['project_id','=',project_selected],['state','!=','bad']];

	$('#gvm_search_product_part option').remove();
	$('#gvm_search_product_part').append('<option id="0" value="0"></option>');
        Part.query(['name']).filter([['project_id','=',project_selected]]).all().then(function(id){
          $.each(id, function(index, item){
            $('#gvm_search_product_part').append('<option id="'+index+'" value="'+item.id+'">'+item.name+'</option>');
	  })
	});
	this.search();
    },
    update_part: function(){
    	var self = this;
	this.search_filter[2] = (['issue','=',$('#gvm_search_product_part option:selected').text()])
	if ($("#gvm_search_product_part option:selected").text() == '')
	{
	  this.search_filter.pop(2);
	}
	this.search();
    },
    search: function(){
    	var self = this;
	self.data = [];
	self.data_id = [];
	self.update_content = [];
	self.Numtmp_row = [];
	self.Numtmp_col = [];
	self.original_data = [];
	var project_selected = $('#gvm_search_product option:selected').text();
	Product.query(
	  ['id','sequence_num','name','product_name','material','original_count','bad_state','purchase_by_maker','etc']
	).filter(self.search_filter).limit(500).all().then(function(id){
	  $.each(id, function(index, item){
	    self.data.push([0, //체크박스
	                    item.sequence_num, 
			    item.name, 
			    item.product_name, 
			    item.material, 
			    item.original_count, 
			    item.etc, 
			    item.bad_state, 
			    item.purchase_by_maker[1]]);
	    self.data_id.push(item.id);
	  })
	});
    },
    loading: function(){
    	var self = this;
        var change = function(instance, cell, value){
          var cellName = $(instance).jexcel('getColumnNameFromId', $(cell).prop('id'));
          $(cell).css('color','red');
	  var cellNum = $(cell).prop('id').split('-')[1];
	  var cellNum_col = $(cell).prop('id').split('-')[0];
	  if (self.Numtmp_row.includes(cellNum) == false){
	    self.Numtmp_row.push(cellNum);
	    self.update_content.push(self.data[cellNum]);
	  }
	  if (self.Numtmp_col.includes(cellNum_col) == false){
	    self.Numtmp_col.push(cellNum_col);
	  }
        }

	if (self.data.length == 0){
	  self.data.push(['0','0']);
	}
	self.$('#mytable').jexcel({
	  data: self.data, 
	  colHeaders: self.colHeaders,
	  colWidths: [30,40,190,140,100,50,100,50,80],
	  onchange: change,
	  columns: [
	    {type: 'checkbox'},
	  ]
	});
    },
    save: function(){
        var self = this;
        var selected_project = $('#gvm_search_product option:selected');
        var selected_part = $('#gvm_search_product_part option:selected');
	var reorder_text = '';
	if (selected_project.text() != false){
	  $.each(self.update_content, function(id,row){
	    reorder_text = '';
	    row[0] = self.data_id[self.Numtmp_row[id]]; 
	    if (row[7] == false){
	      row[7] = 'A';
	    }
	    row[9] = selected_project.text();
	    row[10] = selected_part.text();
	    //$.each(self.Numtmp_col, function(id,col){
	    //  reorder_text += (self.colHeaders[col] + ' : ' + self.original_data[self.Numtmp_row[id]][col] + '->' + row[col] + '\n');
	    //});
	    row[11] = reorder_text;
	    console.log('text= '+reorder_text);
	  });
	  Product.call('gvm_bom_save', ['save',self.update_content]);
	  console.log(self.update_content);
	  alert('save');
	  this.search();
	}else{
	  alert('Please Check Project');
	}
    },
    purchase: function(){
      var self = this;
      var purchase_list = [];
      var selected = $('#gvm_search_product option:selected');
      var selected_part = $('#gvm_search_product_part option:selected');
      if (selected.text() != false){
        $.each(self.data, function(id, row){
  	  row[0] = self.data_id[id]; 
	  row[9] = selected.text();
	  row[10] = selected_part.text();
          if (row[8] == false){
	    purchase_list.push(row);
	  }
        })
      }

      Product.call('gvm_purchase_create',['purchase', purchase_list]);
    }

});

core.form_custom_registry.add('search_table', SearchTable);

});
