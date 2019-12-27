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
        'click #edit_button': function(){this.editable = true; this.loading();},
        'click #gvm_quick_create': 'gvm_quick_create',
    },
    init: function() {
        this._super.apply(this, arguments);
        var self = this;
        this.editable = true;
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
            var tree_test = [];
            $.each(id, function(index, item){
                //tree_test[index] = ({'id':item.id,'title':item.name, 'subs':[], 'rate':1});
                tree_test[index] = ({'id':item.id,'title':item.name, 'rate':1});
            })
            return tree_test;
        }).then(function(ar){
            var sort_array = self.sort_tree(ar);
            var combotree = $('#gvm_search_product').comboTree({
                source: sort_array
            });
        });

        //hide create,close button
        setTimeout(function(){
            var test = $('.modal-title:contains(BOM)')[0].parentElement.nextElementSibling.nextElementSibling.lastElementChild;
            $(test).hide();
        },100);

    },
    // 이름을 기준으로 tree 정렬(ex. ssm ak > ssm ak #1)
    sort_tree: function(project_dic) {
        var second_array = [];
        // id, title, subs, rate
        $.each(project_dic, function(index, item){
            // 자신과 이름이 같은게 있으면 리스트 따로 저장
            var child_project = project_dic.filter(function(c){
                if (c.title != item.title && c.title.indexOf(item.title) != -1){
                    return true;
                }
            })
            if (child_project.length != 0){
                //child_project.map(c=>c.rate = item.id+0.1);
                child_project.map(function(c){
                    c.rate = item.id+0.1;
                })
                item.subs = child_project;
            }
        });

        // rate가 높은것은 project_dic에서 제거
        var tree_array = project_dic.filter(function(c){
            return c.rate == 1;
        });

        return tree_array;
    },
    update_project: function(){ 
        var self = this;
        var project_selected = $('#gvm_search_product.comboTreeInputBox').val();
        this.search_filter = [['project_id','=',project_selected],['state','!=','cancel']];

        // project 변경 시 part 검색 초기화        
        $('#gvm_search_product_part option').remove();
        $('#gvm_search_product_part').append('<option id="0" value="0"></option>');

        var Part = new Model('project.issue');
        Part.query(['name']).filter([['project_id','=',project_selected]]).all().then(function(id){
            $.each(id, function(index, item){
                $('#gvm_search_product_part').append('<option id="'+index+'" value="'+item.id+'">'+item.name+'</option>');
            })
        });
        if (project_selected != ''){
            $('#gvm_quick_create').show();
        }
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
            ['id','sequence_num','name','product_name','material','original_count','bad_state','purchase_by_maker','etc','create_date','state']
            ).filter(self.search_filter).limit(500).all().then(function(id){
            $.each(id, function(index, item){
                //-1표시는 따로 저장
                if (item.sequence_num.toString().indexOf('-') != -1 || item.state == 'bad') {
                    self.sub_data.push([0, //체크박스
                        item.sequence_num,          //1
                        item.name,                  //2
                        item.product_name,          //3
                        item.material,              //4
                        item.original_count,        //5
                        item.etc,                   //6
                        item.bad_state,             //7
                        item.purchase_by_maker[1],  //8
                        item.create_date,           //9
                        ]);
                    self.sub_data_id.push(item.id);
                }else{
                    self.data.push([0, //체크박스
                        item.sequence_num,          //1
                        item.name,                  //2
                        item.product_name,          //3
                        item.material,              //4
                        item.original_count,        //5
                        item.etc,                   //6
                        item.bad_state,             //7
                        item.purchase_by_maker[1],  //8
                        ]);
                    self.data_id.push(item.id);
                }
            })
        }).then(function(){self.loading();});
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
        var td_size = [30,40,190,140,100,50,100,50,80];
        self.$('#mytable').jexcel({
            data: self.data, 
            colHeaders: self.colHeaders,
            colWidths: td_size,
            onchange: change,
            editable: this.editable,
            columns: [
            {type: 'checkbox'},
            {type: 'text'},
            {type: 'text'},
            {type: 'text'},
            {type: 'text'},
            {type: 'text'},
            {type: 'text'},
            {type: 'dropdown', source:['A','B','C','D','E','F','G'] },
            {type: 'text'},
            ]
        });
        var seq_name = '';
        var selected_cel = '';
        var last_element = '';
        var parent_product = '';
        // 수정되었던 자재를 이름순이 아닌  작성시간 순으로 정렬
        self.sub_data.sort(function(a,b){
            if (a[9]>b[9]){ //9 = create_date
                return 1;
            }else{
                return -1;
            }
        });

        $.each(self.sub_data, function(index, value){
            //detail content
            if (value[1] == false){
               return true; 
            };
            seq_name = value[1].split('-')[0]
            selected_cel = $('#mytable tbody td:nth-child(3):contains(' + seq_name + ')')[0];
            if (!selected_cel){return true;}
            parent_product = selected_cel.parentElement;
            last_element = $(parent_product.lastElementChild);
            var td_element = '';
            $.each(value, function(i,item){
                if (i == 0 || i == 9){return true;} //0 = excel cell num, 9 = create_date
                td_element += '<td width="' + td_size[i] + 'px" align="center" style="background-color:#f3f3f3">' + item + '</td>';
            });
            var child_td = '<tr id="row-1000" class="detail_cell" style="display:none; margin:3px">'
                      + '<td style="visibility:hidden;width:34px"></td><td>---</td>'+ td_element + '</tr>';
            $(parent_product).after(child_td);

            //+ button
            if (last_element.hasClass('detail_button') || $(parent_product).hasClass('detail_cell')){
            //버튼이 이미 있거나, 추가된 열인 경우 SKIP
                return true;
            }
            last_element.after('<input type="button" class="detail_button" value="+" id="gvm_excel_add"/>');
        });
        self.detail_toggle = true;
        $('#detail_product_get').html('수정이력보기');
    },
    save: function(){
        var self = this;
        var project_selected = $('#gvm_search_product.comboTreeInputBox').val();
        var selected_part = $('#gvm_search_product_part option:selected');
        var reorder_text = '';
        var save_complete = true;
        if (project_selected != false){
            var check_confirm = confirm('저장하시겠습니까');
            if (check_confirm)
            {
                $.each(self.update_content, function(id,row){
                    if (row[1] == false){
                        alert('번호를 꼭 입력해 주세요');
                        save_complete = false;
                        return false;
                    }
                    reorder_text = '';
                    row[0] = self.data_id[self.Numtmp_row[id]]; 
                    if (row[7] == false){
                        row[7] = 'A';
                    }
                    row[9] = project_selected;
                    row[10] = selected_part.text();
                });
                if (save_complete){
                    Product.call('gvm_bom_save', ['save',self.update_content]).then(function(){
                        self.search()
                    });
                    console.log(self.update_content);
                }
            }
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
                //발주서 생성 시 필요한 정보 입력
                row[0] = self.data_id[id];
                row[9] = project_selected; // 0, 9, 10 에 할당된 게 없어 id, project_id, unit_id 입력
                row[10] = selected_part.text();
                if (row[8] == false){ // 발주서이름이 없는 항목들 모두 발주 내도록 한다
                    purchase_list.push(row);
                }
            })
        }

        Product.call('gvm_purchase_create',['purchase', purchase_list]).then(function(){
            self.search();
        });
    },
    get_all_detail_product: function(){
        var self = this;
        if (self.detail_toggle){
            $('#detail_product_get').html('수정이력숨기기');
            $('.detail_cell').show();
            self.detail_toggle = false;
        }else
        {
            $('#detail_product_get').html('수정이력보기');
            $('.detail_cell').hide();
            self.detail_toggle = true;
        }
    },
    get_detail_product: function(event) {
        var self = this;
        //var parent_product = event.currentTarget.parentElement
        //var seq_name = parent_product.childNodes[2].textContent;
        //var selected_cel = $('#mytable tbody td:nth-child(3):contains(' + seq_name + ')');
        //var sub_filter = self.sub_data.filter(c => c.indexOf(seq_name) != -1);
        //var detail_cell = $(parent_product);

        //if (detail_cell.css('display') == 'none'){
        //    detail_cell.show();
        //}else{
        //    detail_cell.hide();
        //}
    },
    add_excel: function(){
        self.$('#mytable').jexcel('insertRow',1);
    },
    gvm_quick_create: function(){
        var self = this;
        var project_id = '';
        var name = '';
        var model = '';

        var project_selected = $('#gvm_search_product.comboTreeInputBox').val();
        var Project = new Model('project.project');
        var project_id = Project.query(['id']).filter([['name','=',project_selected]]).all().then(function(id){
            var prj_id = id[0].id;
            var model_obj = new Model('ir.model.data');
            model_obj.call('get_object_reference', ['project','project_product_view_form_simplified']).then(function(result){
                var view_id = result[1];
                var ctx = {
                    'view_product_menu':0
                }
                var action = {
                    type: 'ir.actions.act_window',
                    res_model: 'project.project',
                    res_id: prj_id,
                    view_mode: 'form',
                    target: 'new',
                    view_type: 'form',
                    context: ctx,
                    views: [[view_id,'form']],
                };
                self.do_action(action);
            });
        })
        //new data.DataSet(this, model, undefined)
        //        .create({'name':name,'project_id':project_id,'user_id':1,'stage_id':18}, undefined);
    },
});

core.form_custom_registry.add('search_table', SearchTable);

});

