# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time
import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.tools.translate import _
from odoo.tools.sql import drop_view_if_exists
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class GvmMarketing(models.Model):
    _name = "gvm.marketing"
    _description = "marketing"
    _order = 'name'

    name = fields.Char(string='프로젝트명')
    color = fields.Integer(string='color')
    site = fields.Char(string='사이트')
    project_code = fields.Char(string='프로젝트코드')
    num = fields.Integer(string='number')
    attachment = fields.Many2many('ir.attachment', domain="[('res_model','=','gvm.marketing')]", string='첨부파일')
    lines = fields.One2many('gvm.marketing.line','marketing','line')
    date_to = fields.Date(string='시작일')
    date_end = fields.Date(string='마감일')

class GvmMarketingLine(models.Model):
    _name = "gvm.marketing.line"
    _description = "marketing_line"
    

    name = fields.Char(string='name')
    marketing = fields.Many2one('gvm.marketing','marketing')
    date_to = fields.Date(string='시작일')
    date_end = fields.Date(string='마감일')
    text = fields.Text(string='내용')
