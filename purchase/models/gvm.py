# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime,timedelta
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_is_zero, float_compare
from odoo.exceptions import UserError, AccessError
from odoo.tools.misc import formatLang
from odoo.addons.base.res.res_partner import WARNING_MESSAGE, WARNING_HELP
from odoo.http import content_disposition, dispatch_rpc, request
import odoo.addons.decimal_precision as dp
import logging
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

_logger = logging.getLogger(__name__)
class GvmDelivery(models.Model):
    _name = "gvm.delivery"
    _description = "gvm_delivery"

    @api.model
    def default_sequence(self):
        _logger.warning("sequence%s"%self.env['ir.sequence'].next_by_code('gvm.delivery'))
        return  self.env['ir.sequence'].next_by_code('gvm.delivery')

    de_num = fields.Char('택배번호', required=True, index=True, copy=False, default='New')
    attachment = fields.Many2many('ir.attachment',domain="[('res_model','=','gvm.delivery')]", string='명세서')
    release = fields.Selection([('company','사내'),('SDV','SDV'),('SSM','SSM'),('internal','국내')], string='출고지', default='SSM')
    release_action = fields.Selection([('handcarry','핸드캐리'),('delivery','택배')], string='출고', default='handcarry')
    arrival_date = fields.Date('도착예정일자', default=datetime.today())
    release_date = fields.Date('출고일자',default=datetime.today())
    release_man = fields.Many2one('res.users','출고자',default=lambda self:self.env.uid)
    permit_man = fields.Many2one('res.users','검토자')
    field_order_man = fields.Many2one('res.users','현지요청자',default=lambda self:self.env.uid)
    within_order_man = fields.Many2one('res.users','사내요청자',default=lambda self:self.env.uid)
    handcarry_man = fields.Many2one('res.users','핸드캐리담당자')
    delivery_number = fields.Char('송장번호')
    delivery = fields.Many2many('gvm.product', string='product')
    state = fields.Selection([
        ('write', '작성'),
        ('send_ready', '발송준비중'),
        ('sending', '발송중'),
        ('send', '발송완료'),
        ('cancel', '취소')
        ], string='Status', readonly=True, index=True, copy=False, default='write', track_visibility='onchange')

    @api.model
    def create(self, vals):
        if vals.get('de_num','New') == 'New':
            vals['de_num'] = self.env['ir.sequence'].next_by_code('gvm.delivery') or '/'
        res = super(GvmDelivery, self).create(vals)
        self.write({'state': 'send_ready'})
        return res

    @api.multi
    def button_done(self):
        self.write({'state': 'send'})
        return {}

    @api.multi
    def button_confirm(self):
        self.write({'state': 'send_ready'})
        return {}

    @api.multi
    def button_cancel(self):
        self.write({'state': 'cancel'})
        return {}

    @api.multi
    def button_resend(self):
        self.write({'state': 'send_ready'})
        return {}

    @api.multi
    def button_send(self):
        self.write({'state': 'sending'})
        return {}

class GvmProduct(models.Model):
    _name = "gvm.product"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = "gvm_product"
    _order = 'create_date, sequence_num, name, product_name'

    #택배
    purchase_num = fields.Char('구매 번호')
    before_weight = fields.Char('포장 전 무게')
    after_weight = fields.Char('포장 후 무게')
    weight_state = fields.Selection([('normal','정상'),('abnormal','확인필요')],string='무게비교',readonly=True)

    de_num = fields.Char('택배번호', readonly=True)
    name = fields.Char('도면번호/규격',index=True, copy=False)
    product_id = fields.Many2one('product.product','product_id')
    project_ids = fields.Many2one('project.project','project_id', store=True, compute='_compute_project_name')
    project_set = fields.Many2many('project.project',string='project_set', compute='_compute_project_name',store=True)
    purchase = fields.Many2one('purchase.order','purchase')
    purchase_by_maker = fields.Many2one('gvm.purchase_product','설계발주번호')
    #part = fields.Many2one('project.task','part', compute='_compute_part')
    #issue = fields.Many2one('project.issue','issue',compute='_compute_issue',store=True)
    part = fields.Many2one('project.task',string='유닛')
    issue = fields.Many2one('project.issue',string='파트')

    category = fields.Selection([('1','기구/가공품'),('2','기구/요소품'),('3','전장/가공품'),('4','전장/요소품'),('5','기타')],string="분류")
    #project_id = fields.Char('프로젝트',copy=False,store=True, compute='_compute_project_name')
    project_id = fields.Char('프로젝트')
    part_name = fields.Char('파트', store=True, compute='_compute_part_name')
    product_name = fields.Char('품명')
    original_count = fields.Integer('원수',default=1)
    total_count = fields.Integer('총 발주 수', compute='_compute_total_count')
    material = fields.Char('재질')
    order_man = fields.Char('발주요청자',translate=True)
    drawing_man = fields.Char('설계자',translate=True)
    destination_man = fields.Char('입고자')
    request_date = fields.Date('설계요청 납기일자',required=True)
    expected_date = fields.Date('입고예정일자')
    destination_date = fields.Date('입고일자')
    receiving_date = fields.Date('출고일자')
    request_receiving_man = fields.Char('출고요청자')
    receiving_man = fields.Char('출고자')
    reorder_num = fields.Char('A')
    reorder_text = fields.Html('사유')
    price = fields.Integer('단가')
    total_price = fields.Integer('총액', compute='_compute_total_price')
    tax_price = fields.Integer('합계', compute='_compute_tax', store=True)
    department = fields.Char('부서',store=True, compute='_compute_department')
    exid = fields.Char('이름',compute='_compute_xml_id')
    known_price = fields.Integer('이전 가격',compute='_compute_set_price')
    etc = fields.Char('이슈사항 및 재발주요청사유')
    state = fields.Selection([
        ('all', 'All'),
        ('done', '출고'),
	('keep','보류'),
	('unkeep','보류해제'),
        ('no', '작성됨'),
        ('purchase', '발주'),
        ('purchasing', '발주진행중'),
        ('purchase_complete', '발주완료'),
	('bad','불량'),
	('return','반품'),
	('delete','삭제'),
	('cancel','발주취소'),
        ('request_receiving', '출고요청'),
        ('destination', '입고')
        ], string='Status', default='no',track_visibility="onchange")
    partner_id = fields.Char('업체명',store=True, compute='_compute_partner')
    partner_ids = fields.Many2one('res.partner','업체',domain='[("supplier","=",True)]')
    sequence_num = fields.Char('번호')
    purchase_order_new = fields.Boolean('new_purchase')
    attachment = fields.Many2many('ir.attachment', domain="[('res_model','=','gvm.product')]", string='도면', compute='_compute_attachment')
    title = fields.Boolean('invisible')
    emergency = fields.Boolean('긴급',default=False,store=True)
    draft_request_date = fields.Date('견적요청일자')
    return_date = fields.Date('반품일자')
    complete_date = fields.Date('양품확인 완료일자')
    order_date = fields.Date('발주일자')
    draft_partner_ids = fields.Many2one('res.partner','견적업체',domain='[("supplier","=",True)]')
    bad_item = fields.Boolean('불량', default=False)
    stock_item = fields.Boolean('재고', default=False)
    bad_state = fields.Selection([
        ('A', '정상'),
        ('B', '가공불량'),
        ('C', '설계불량'),
	('D', '작업자 파손'),
	('E', '구매불량'),
	('F', '분실'),
	('G', '업체미스'),
	], string='불량유형', default='A')
    release_place = fields.Many2one('gvm.delivery.release',string='출고지')
    sub_id = fields.Char('sub_id')

    def _generate_order_by(self, order_spec, query):
	my_order = "case when substring(sequence_num from '^P') IS NULL then substring(sequence_num from '^\d+$')::int end, sequence_num"
	if order_spec:
	   _logger.warning(order_spec)
	   return super(GvmProduct,self)._generate_order_by(order_spec,query) + "," + my_order
	return " order by " + my_order

    def _compute_xml_id(self):
        res = self.get_external_id()
        for record in self:
            record.exid = res.get(record.id)
    
    @api.depends('purchase_by_maker.attachment')
    def _compute_attachment(self):
      for record in self:
       attachment_list = record.purchase_by_maker.attachment
       if attachment_list:
        for att in attachment_list:
	 if record.name:
           if att.name.find(record.name) != -1:
             record.attachment = att

    @api.depends('name')
    def _compute_set_price(self):
     for record in self:
       value = ''
       if record.name:
            value = record.name
            record.known_price = self.search(['|',('name','ilike',value),('price','!=','0')], limit=1).price

    @api.depends('total_count','price')
    def _compute_total_price(self):
     for record in self:
      record.total_price = record.total_count * record.price

    @api.depends('total_price')
    def _compute_tax(self):
     for record in self:
      record.tax_price = record.total_price + record.total_price * 0.1

    @api.depends('purchase_by_maker.project_id')
    def _compute_project_name(self):
      for record in self:
        record.project_id = record.purchase_by_maker.project_id.name
        record.project_ids = record.purchase_by_maker.project_id.id
	if record.purchase_by_maker.project_ids:
	  record.project_set = record.purchase_by_maker.project_ids
	else:
	  record.project_set = record.purchase_by_maker.project_id
        # 같은 이름 있으면 기존 제품은 불량으로 변경
        if record.reorder_num != 'A':
	  same_product = self.env['gvm.product'].search([('project_id','=',record.project_id),('name','=',record.name)])
	  if same_product:
	    for sp in same_product:
	      sp.state = 'bad'

    @api.depends('purchase_by_maker.part')
    def _compute_part_name(self):
     for record in self:
      record.part_name = record.purchase.part['name']

    @api.depends('purchase_by_maker.department')
    def _compute_department(self):
     for record in self:
      record.department = record.purchase_by_maker.department

    @api.depends('purchase_by_maker.partner_id','partner_ids')
    def _compute_partner(self):
     for record in self:
      record.partner_id = record.purchase_by_maker.partner_id.name
      if record.partner_ids:
        record.partner_id = record.partner_ids.name

    @api.depends('purchase_by_maker.create_uid','purchase_by_maker.order_man','purchase_by_maker.drawing_man')
    def _compute_order_man(self):
     for record in self:
      if record.purchase.order_man:
       record.order_man = record.purchase_by_maker.order_man.name
       record.drawing_man = record.purchase_by_maker.drawing_man.name
      else:
       record.order_man = record.purchase_by_maker.create_uid.name
       record.drawing_man = record.purchase_by_maker.create_uid.name
    
    @api.depends('purchase_by_maker.line_count','original_count')
    def _compute_total_count(self):
     for record in self:
      record.total_count = record.purchase_by_maker.line_count * record.original_count

    @api.depends('part_name','purchase.project_id.tasks')
    def _compute_part(self):
     for record in self:
      part_name = record.part_name
      for part in record.purchase.project_id.tasks:
       if part_name == part['name']:
	record.part = part

    @api.depends('purchase_by_maker','purchase_by_maker.project_id.issue_ids')
    def _compute_issue(self):
     for record in self:
      part_name = record.purchase_by_maker.issue.name
      for part in record.purchase_by_maker.project_id.issue_ids:
       if part_name == part['name']:
        record.issue = part

    @api.multi
    def button_destination(self):
        self.write({'destination_date': datetime.today(), 
	            'destination_man': self.env.user.name,
		    'state': 'destination'})
        return {}

    @api.multi
    def button_request_receiving(self):
        self.write({'request_receiving_man': self.env.user.name,
	            'state': 'request_receiving'})
        return {}

    @api.multi
    def button_receiving(self):
        self.write({'receiving_man': self.env.user.name,
	            'receiving_date': datetime.today(),
	            'state': 'done'})
        return {}

    @api.onchange('destination_date')
    def _onchange_destination_date(self):
      for record in self:
        if record.destination_date:
	  record.destination_man = self.env.user.name
          record.state = 'destination'

    @api.onchange('receiving_date')
    def _onchange_receiving_date(self):
      for record in self:
        if record.receiving_date:
          record.state = 'done'
  	  record.receiving_man = self.env.user.name

    @api.multi
    def purchase_view(self):
        return {
            'name': _('Purchase Order'),
            'domain': '[("state","=","write")]',
            'res_model': 'gvm.purchase_product',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'limit': 80,
            'context': "{}"
        }

    @api.multi
    def purchase_project_view(self):
        cc = {'active_id':'21'}
        return {
            'domain': ['id','=',21],
            'name': _('Project Manage'),
            'res_model': 'project.project',
            'res_id':21,
            'type': 'ir.actions.act_window',
            'view_id': False,
            'views': [[False,'form']],
            'target': 'new',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'limit': 80,
            'context': {},
            }
        

    def gvm_bom_save(val1, vals):
    	Product = request.env['gvm.product']
    	Project = request.env['project.project']
	Part = request.env['project.issue']
	column = ['id','sequence_num','name','product_name','material','original_count', 'etc']
	ko_column = ['id','번호','도번 및 규격','품명','재질','원수', '비고']
	if vals:
	  project_id = Project.search([('name','=',vals[0][9].encode('utf-8'))]).id
	  part_id = Part.search([('name','=',vals[0][10].encode('utf-8')),('project_id','=',project_id)]).id
        for val in vals:
          product_id = val[0]
          product_sequence_num = val[1]
          product_main_name = val[2].encode('utf-8')
          product_name = val[3].encode('utf-8')
          product_material = val[4].encode('utf-8')
          product_original_count = val[5]
          product_etc = val[6].encode('utf-8')
          product_bad_state = val[7]
          product_project_id = val[9].encode('utf-8')

          # 수정 시 표시 붙여주기
	  if (product_bad_state == False or product_bad_state.upper().encode('utf-8') == 'FALSE'):
	    product_bad_state = 'A'
	  if str(product_id) != 'None':
            Update = Product.search([('id','=',product_id)])
            product_seq_num = '' 
            if Update.sequence_num:
                if Update.sequence_num.find('-') != -1:
                  seq = Update.sequence_num.split('-') # 1-1
                  product_seq_num = seq[0] + '-' + str((int(seq[1]) + 1))
                else:
                  product_seq_num = Update.sequence_num + '-' + '1'

            # reorder text
            reorder_text = Update.reorder_text or ''
            product_object = ''
            # 검토완료되지 않은 자재는 바로 수정되도록
            if Update.state == 'no':
                product_object = Update
            # 검토완료된 자재는 기존 자재는 불량으로 변경 후 새로 생성
            else:
                if product_bad_state.upper().encode('utf-8') == Update.bad_state:
                    raise UserError(_('상태 수정이 필요합니다'))
                product_object = Product.create({'name': product_main_name})
                Update.write({
                    'state' : 'bad',
                    'bad_state': product_bad_state.upper().encode('utf-8'), 
                    'sequence_num': product_seq_num,
                })
                # 수정된 자재의 발주서에 표시
                if Update.purchase_by_maker:
                    Update.purchase_by_maker.state = 'modify'

            for i in range(1,7):
              text = ''
              if str(Update[column[i]]) != val[i] and not i==1:
                text = str('%s : %s -> %s (%s)' 
                    % ( str(unicode(ko_column[i])), Update[column[i]], val[i], str(datetime.today())[0:10]))
                reorder_text += text
                reorder_text += '<br><br>'

              product_object.write({
                column[i] : val[i],
              })
            Update.write({'reorder_text':reorder_text})
            ##같은이름의 같은프로젝트에 있는 자재에 모두 이력을 쓰도록 해야겠다
            product_object.write({'reorder_text':reorder_text, 
                         'project_id': product_project_id,
                         'bad_state': product_bad_state.upper().encode('utf-8'), 
                         'etc': product_etc,
                         'issue':part_id, 
                         'project_ids': project_id, 
                         'project_set':[(4, project_id)], 
                         'request_date':datetime.today() + timedelta(days=7),
                         'order_man':request.env.user.name})
	  else:
	    PONum = Product.create({
	    		'sequence_num':val[1],
	    		'name': product_main_name,
	    		'product_name': product_name,
			'bad_state': product_bad_state.upper().encode('utf-8'), 
			'material': product_material,
			'original_count': product_original_count,
			'project_id': product_project_id,
			'project_ids': project_id, 
			'issue':part_id,
			'request_date':datetime.today() + timedelta(days=7),
			'order_man':request.env.user.name,
                        'etc':product_etc,
	    })
	    PONum.write({
			'project_set':[(4, project_id)],
	    })

    def update_check(check_list):
        return text

    def gvm_purchase_create(val1, vals):
        Purchase = request.env['gvm.purchase_product']
    	Project = request.env['project.project']
    	Part = request.env['project.issue']
	part_id = ''
        newPo = ''
	if vals:
	  project_id = Project.search([('name','=',vals[0][9])]).id
	  part_id = Part.search([('name','=',vals[0][10]),('project_id','=',project_id)]).id
          newPo = Purchase.create({
	           'project_id':project_id,
                   'partner_id':1013,
                   'line_count':1,
                   #'attachment':self.attachment,
                   'issue':part_id,
		   'drawing_man':request.env.uid,
                  })
          for np in vals:
	    newPo.write({'product':[(4, int(repr(np[0]).encode('utf-8')))]})

class GvmProductReleasePlace(models.Model):
    _name = "gvm.product.release"
    _description = "gvm_product"
    _order = 'name'
    
    name = fields.Char('name',index=True, copy=False)
    method = fields.Char('method')

    @api.multi
    def name_get(self):
        res = []
        for category in self:
	  name = category.name
	  if category.method:
	    name = name + ' / ' + category.method
          res.append((category.id, name))
        return res

