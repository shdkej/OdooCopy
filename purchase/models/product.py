# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_is_zero, float_compare
from odoo.exceptions import UserError, AccessError
from odoo.tools.misc import formatLang
from odoo.addons.base.res.res_partner import WARNING_MESSAGE, WARNING_HELP
import odoo.addons.decimal_precision as dp
import logging

_logger = logging.getLogger(__name__)
class GvmProductInherit(models.Model):
    _inherit = 'product.product'
    _description = "gvm_product_inherit"
    
    product_ids = fields.Many2one('gvm.product','product')
    project_ids = fields.Many2one('project.project','프로젝트_id', store=True, compute='_compute_project_name')
    project_set = fields.Many2many('project.project',string='project_set', compute='_compute_project_name',store=True)
    purchase = fields.Many2one('purchase.order','purchase')
    part = fields.Many2one('project.task','part', compute='_compute_part')
    issue = fields.Many2one('project.issue','issue',compute='_compute_issue',store=True)

    project_id = fields.Char('프로젝트',copy=False,store=True, compute='_compute_project_name')
    part_name = fields.Char('파트', store=True, compute='_compute_part_name')
    product_name = fields.Char('품명')
    drawing = fields.Char('도면번호')
    specification = fields.Char('규격')
    material = fields.Char('재질')
    order_man = fields.Char('발주요청자',translate=True,compute='_compute_order_man')
    destination_man = fields.Char('입고자')
    expected_date = fields.Date('예정일자')
    destination_date = fields.Date('입고일자')
    receiving_date = fields.Date('출고일자')
    request_receiving_man = fields.Char('출고요청자')
    receiving_man = fields.Char('출고자')
    reorder_num = fields.Char('A')
    reorder_text = fields.Char('사유')
    department = fields.Char('부서',store=True, compute='_compute_department')
    exid = fields.Char('이름',compute='_compute_xml_id')
    etc = fields.Char('비고')
    state = fields.Selection([
        ('all', 'All'),
        ('done', '출고'),
	('keep','보류'),
	('unkeep','보류해제'),
        ('no', '발주'),
	('bad','불량'),
	('delete','삭제'),
        ('request_receiving', '출고요청'),
        ('destination', '입고'),
        ('paydone','지급완료')
        ], string='Status', default='no')
    partner_id = fields.Char('업체명',store=True, compute='_compute_partner')
    partner_ids = fields.Many2one('업체', compute='_compute_partner')
    sequence_num = fields.Char('번호')
    category = fields.Char('분류',compute='_compute_category',store=True)
    purchase_order_new = fields.Boolean('new_purchase')
    attachment = fields.Many2many('ir.attachment', domain="[('res_model','=','gvm.product')]", string='도면', compute='_compute_attachment')
    title = fields.Boolean('invisible')
    emergency = fields.Boolean('긴급',defualt=False,store=True)


    def _generate_order_by(self, order_spec, query):
	my_order = "issue asc, case when substring(sequence_num from '^P') IS NULL then substring(sequence_num from '^\d+$')::int end, sequence_num"
	if order_spec:
	   return super(GvmProduct,self)._generate_order_by(order_spec,query) + "," + my_order
	return " order by " + my_order

    def _compute_xml_id(self):
        res = self.get_external_id()
        for record in self:
            record.exid = res.get(record.id)

    @api.depends('purchase')
    def _compute_attachment(self):
      for record in self:
       attachment_list = record.purchase.attachment
       if attachment_list:
        for att in attachment_list:
         if att.name.find(record.name) != -1:
           record.attachment = att

    @api.depends('purchase.project_id.name')
    def _compute_project_name(self):
      for record in self:
        record.project_id = record.purchase.project_id.name
        record.project_ids = record.purchase.project_id.id
	if record.purchase.project_ids:
	  record.project_set = record.purchase.project_ids
	else:
	  record.project_set = record.purchase.project_id
        if record.reorder_num != 'A':
	  same_product = self.env['gvm.product'].search([('project_id','=',record.project_id),('name','=',record.name)])
	  if same_product:
	    for sp in same_product:
	      sp.state = 'bad'

    @api.depends('purchase.part')
    def _compute_part_name(self):
     for record in self:
      record.part_name = record.purchase.part['name']

    @api.depends('purchase.department')
    def _compute_department(self):
     for record in self:
      record.department = record.purchase.department

    @api.depends('purchase.partner_id','partner_ids')
    def _compute_partner(self):
     for record in self:
      record.partner_id = record.purchase.partner_id.name
      if record.partner_ids:
        record.partner_id = record.partner_ids.name

    @api.depends('purchase.create_uid','purchase.order_man')
    def _compute_order_man(self):
     for record in self:
      if record.purchase.order_man:
       record.order_man = record.purchase.order_man.name
      else:
       record.order_man = record.purchase.create_uid.name

    @api.depends('purchase.category')
    def _compute_category(self):
     for record in self:
      record.category = record.purchase.category

    @api.depends('part_name','purchase.project_id.tasks')
    def _compute_part(self):
     for record in self:
      part_name = record.part_name
      for part in record.purchase.project_id.tasks:
       if part_name == part['name']:
	record.part = part

    @api.depends('purchase','purchase.project_id.issue_ids')
    def _compute_issue(self):
     for record in self:
      part_name = record.purchase.issue.name
      for part in record.purchase.project_id.issue_ids:
       if part_name == part['name']:
        record.issue = part

    @api.multi
    def button_destination(self):
        self.write({'destination_date': datetime.today(), 
	            'destination_man': self.env.user.name,
		    'state': 'destination'})
        return {}
    
    @api.multi
    def button_paydone(self):
        self.write({'state': 'paydone'})
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

    @api.onchange('product_ids')
    def _onchange_product(self):
      for record in self:
         record.name = self.product_ids.name
         record.product_name = self.product_ids.product_name
         record.specification = self.product_ids.specification
         record.order_man = self.env.uid
         record.etc = self.product_ids.etc
         record.material = self.product_ids.material
         record.request_date = datetime.today()
	 
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
