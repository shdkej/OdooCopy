# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time
import logging
from datetime import datetime
import datetime as dt
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.tools.translate import _
from odoo.tools.sql import drop_view_if_exists
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import xlwt
import os
from cStringIO import StringIO

import re
from odoo.http import request

_logger = logging.getLogger(__name__)

class GvmMrp(models.Model):
    _name = "gvm.mrp"
    _description = "Product Management"
    _order = 'priority, sequence, num'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char(string='sign',required=True)
    sequence = fields.Integer(default=1)
    date = fields.Date(string='date')
    num = fields.Integer(string='number')
    color = fields.Integer('Color')
    site = fields.Many2one('project.site', string='사이트')
    project_sub = fields.One2many('gvm.mrp.sub','main_mrp',string='세부')
    priority = fields.Selection([
            ('0','Normal'),
            ('1','High')
        ], default='0', index=True)

class GvmMrpSub(models.Model):
    _name = "gvm.mrp.sub"
    _description = "PM projetc sub"
    _order = 'priority, sequence, create_date, date'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char(string='name',required=True)
    sequence = fields.Integer(default=1)
    date = fields.Date(string='date')
    cost = fields.Integer('cost')
    description = fields.Char(string='description')
    ratio = fields.Float('환율',default='1')
    card = fields.Selection([('personal','개인'),('corporation','법인')],default='personal')
    color = fields.Integer('Color')
    main_mrp = fields.Many2one('gvm.mrp', string='프로젝트')
    task = fields.Many2one('gvm.mrp.task', string='단계')
    content = fields.One2many('gvm.mrp.content','sub_mrp',string='내용')
    attachment = fields.Many2many('ir.attachment', domain="[('res_model','=','gvm.mrp.sub')]", string='파일')
    priority = fields.Selection([
            ('0','Normal'),
            ('1','High')
        ], default='0', index=True)

class GvmMrpTask(models.Model):
    _name = "gvm.mrp.task"
    _description = "Product Management Task"
    _order = 'num'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char(string='sign',required=True)
    num = fields.Integer(string='number')
    color = fields.Integer('Color')

class GvmMrpContent(models.Model):
    _name = "gvm.mrp.content"
    _description = "PM project Content"
    _order = 'create_date, date'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char(string='제목',required=True)
    date = fields.Date(string='date')
    date_from = fields.Datetime(string='시작시점')
    date_to = fields.Datetime(string='종료시점')
    content = fields.Char(string='내용')
    description = fields.Char(string='특이사항')
    worker = fields.Many2many('hr.employee',string='작업자')
    client = fields.Char('담당자')
    color = fields.Integer('Color')
    main_mrp = fields.Many2one('gvm.mrp',string='프로젝트')
    sub_mrp = fields.Many2one('gvm.mrp.sub',string='세부')
    attachment = fields.Many2many('ir.attachment', domain="[('res_model','=','gvm.mrp.sub')]", string='파일')
    sub_attachment = fields.Many2many('ir.attachment', domain="[('res_model','=','gvm.mrp.sub')]", string='파일', compute='_compute_attachment')

    @api.depends('sub_mrp')
    def _compute_attachment(self):
      for record in self:
        attachment_list = record.sub_mrp.attachment
        if attachment_list:
	  at_list = []
          for att in attachment_list:
	    at_list.append(att.id)
          record.sub_attachment = at_list
