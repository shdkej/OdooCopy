# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import smtplib
from email.mime.text import MIMEText
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

from bs4 import BeautifulSoup
from selenium import webdriver
import re


_logger = logging.getLogger(__name__)

class GvmProject(models.Model):
    _name = "gvm.project"
    _description = "GVM Project"
    _order = 'num'

    num = fields.Integer(string='number')
    name = fields.Char(string='sign')
    project = fields.Many2one('project.project','project')
    sign = fields.Many2many('gvm.signcontent',string='sign', compute='_compute_sign', domain='[("sign_ids","=",3)]')
    total_sign_price = fields.Integer('출장비',compute='_compute_total_sign')
    product = fields.Many2many('gvm.product', string='product', compute='_compute_sign')
    total_product_price = fields.Integer('자재비',compute='_compute_total_sign')

    @api.depends('project')
    def _compute_sign(self):
      for record in self:
        if record.project:
          record.sign = self.env['gvm.signcontent'].search([('project','=',record.project.id)])
          record.product = self.env['gvm.product'].search([('project_set','in',record.project.id)])
	  record.name = record.project.name

    @api.depends('sign')
    def _compute_total_sign(self):
      for record in self:
        total_sign_price = 0
        for sign in record.sign:
	  if sign.sign_ids == 3:
	    sign_cost = sign.had_cost - sign.finally_cost
	    total_sign_price = total_sign_price + sign_cost
        total_product_price = 0
        for product in record.product:
	  total_product_price = total_product_price + product.total_price
        record.total_sign_price = total_sign_price
        record.total_product_price = total_product_price
