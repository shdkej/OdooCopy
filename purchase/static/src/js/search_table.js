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
        'click #detail_product_get': 'get_all_detail_product',
        'click #gvm_excel_add': 'get_detail_product',
        'click #add_product': 'add_excel',
    },
    init: function() {
        this._super.apply(this, arguments);
        var self = this;
        this.tree_data = [];
        var tree_data_array = [];
        this.data = [];
        this.sub_data = [];
        this.data_id = [];
        this.sub_data_id = [];
        this.update_content = [];
        this.search_filter = [];
        this.Numtmp_row = [];
        this.Numtmp_col = [];
        this.original_data = [];
        this.detail_toggle = true;
        this.colHeaders = ['O','번호','도번 및 규격','품명','재질','원수','비고','상태','발주서번호'];

        var Project = new Model('project.project');
        Project.query(['name','project_rate']).filter([['is_finish','=',false]]).all().then(function(id){
            $.each(id, function(index, item){
                tree_data_array.push({'id':item.id,'title':item.name, 'subs':[], 'rate':1});
            })
        });

        this.tree_data = tree_data_array;

        //var sort_array = this.sort_tree(tree_data_array);
        tree_data_array.forEach(function (item, index, array){
            console.log(index);
        });
        var sort_array = tree_data_array;
        //button create
        //button hide
        setTimeout(function(){
            $('.o_form_button_save').hide();
            $('.o_form_button_cancel').hide();
            var combotree = $('#gvm_search_product').comboTree({
                source: sort_array
            });
        },300);

    },
    update_project: function(){
        var self = this;
        var project_selected = $('#gvm_search_product.comboTreeInputBox').val();
        this.search_filter = [['project_id','=',project_selected],['state','!=','cancel']];
        
        $('#gvm_search_product_part option').remove();
        $('#gvm_search_product_part').append('<option id="0" value="0"></option>');
        var Part = new Model('project.issue');
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
        self.sub_data = [];
        self.data_id = [];
        self.sub_data_id = [];
        self.update_content = [];
        self.Numtmp_row = [];
        self.Numtmp_col = [];
        self.original_data = [];
        self.detail_product = [];
        var project_selected = $('#gvm_search_product.comboTreeInputBox').val();
        Product.query(
            ['id','sequence_num','name','product_name','material','original_count','bad_state','purchase_by_maker','etc']
            ).filter(self.search_filter).limit(500).all().then(function(id){
            $.each(id, function(index, item){
                //-1표시는 따로 저장
                if (item.sequence_num.toString().indexOf('-') != -1) {
                    self.sub_data.push([0, //체크박스
                        item.sequence_num, 
                        item.name, 
                        item.product_name, 
                        item.material, 
                        item.original_count, 
                        item.etc, 
                        item.bad_state, 
                        item.purchase_by_maker[1]]);
                    self.sub_data_id.push(item.id);
                }else{
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
                }
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
        var on_load = function(instance, cell, value){
            var child_product = $('<span>123456</span>');
            var parent_product = $('#mytable tbody .jexcel_label');
        };

        if (self.data.length == 0){
            self.data.push(['0','0']);
        }
        var td_size = [30,40,190,140,100,50,100,50,80];
        self.$('#mytable').jexcel({
            data: self.data, 
            colHeaders: self.colHeaders,
            colWidths: td_size,
            onchange: change,
            columns: [
            {type: 'checkbox'},
            ]
        });
        var seq_name = '';
        var selected_cel = '';
        var last_element = '';
        var parent_product = '';
        $.each(self.sub_data, function(index, value){
            //detail content
            seq_name = value[1].split('-')[0]
            selected_cel = $('#mytable tbody td:nth-child(3):contains(' + seq_name + ')')[0];
            if (!selected_cel){return true;}
            parent_product = selected_cel.parentElement;
            last_element = $(parent_product.lastElementChild);
            var td_element = '';
            $.each(value, function(i,item){
                if (i == 0){return true;}
                td_element += '<td width="' + td_size[i] + 'px" align="center" style="background-color:#f3f3f3">' + item + '</td>';
            });
            var test = '<tr id="row-1000" class="detail_cell" style="display:none; margin:3px">'
                      + '<td style="visibility:hidden;width:34px"></td><td>---</td>'+ td_element + '</tr>';
            $(parent_product).after(test);

            //+ button
            if (last_element.hasClass('detail_button') || $(parent_product).hasClass('detail_cell')){
            //버튼이 이미 있거나, 추가된 열인 경우 SKIP
                return true;
            }
            last_element.after('<input type="button" class="detail_button" value="+" id="gvm_excel_add"/>');
        });
    },
    save: function(){
        var self = this;
        var project_selected = $('#gvm_search_product.comboTreeInputBox').val();
        var selected_part = $('#gvm_search_product_part option:selected');
        var reorder_text = '';
        if (project_selected != false){
            $.each(self.update_content, function(id,row){
                reorder_text = '';
                row[0] = self.data_id[self.Numtmp_row[id]]; 
                if (row[7] == false){
                    row[7] = 'A';
                }
                row[9] = project_selected;
                row[10] = selected_part.text();
                //$.each(self.Numtmp_col, function(id,col){
                //  reorder_text += (self.colHeaders[col] + ' : ' + self.original_data[self.Numtmp_row[id]][col] + '->' + row[col] + '\n');
                //});
                //row[11] = reorder_text;
                console.log('update = '+ self.update_content);
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
        var project_selected = $('#gvm_search_product.comboTreeInputBox').val();
        var selected_part = $('#gvm_search_product_part option:selected');
        if (project_selected != false){
            $.each(self.data, function(id, row){
                row[0] = self.data_id[id]; 
                row[9] = project_selected;
                row[10] = selected_part.text();
                if (row[8] == false){
                    purchase_list.push(row);
                }
            })
        }

        Product.call('gvm_purchase_create',['purchase', purchase_list]);
    },
    get_all_detail_product: function(){
        var self = this;
        if (self.detail_toggle){
            $('.detail_cell').show();
            self.detail_toggle = false;
        }else
        {
            $('.detail_cell').hide();
            self.detail_toggle = true;
        }
    },
    get_detail_product: function(event) {
        var self = this;
        var parent_product = event.currentTarget.parentElement
        var seq_name = parent_product.childNodes[2].textContent;
        console.log(seq_name);
        var selected_cel = $('#mytable tbody td:nth-child(3):contains(' + seq_name + ')');
        var detail_cell = $(parent_product);
        //if (detail_cell.css('display') == 'none'){
        //    detail_cell.show();
        //}else{
        //    detail_cell.hide();
        //}
    },
    add_excel: function(){
        self.$('#mytable').jexcel('insertRow',1);
    },
});

core.form_custom_registry.add('search_table', SearchTable);

});

