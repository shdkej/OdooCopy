# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api,fields, models
import logging

_logger = logging.getLogger(__name__)


class GvmProjectIssue(models.Model):
    _inherit = 'project.issue'

    product = fields.One2many('gvm.product','issue','product',store=True)
    product_set = fields.Many2many('gvm.product',string='product_set',compute='_compute_product_set')
    product_confirm = fields.Integer('confirm',compute='_compute_confirm')
    percent = fields.Float('percent',compute='_compute_percent',store=True)

    @api.depends('product')
    def _compute_percent(self):
     for record in self:
      cal = record.product
      total = len(cal)
      a = 0
      for c in cal:
       if c.destination_date:
        a += 1
      if cal:
       record.percent = float(a)/float(total)*100

    @api.depends('product')
    def _compute_confirm(self):
      for record in self:
        if record.product:
          record.product_confirm = 1
        else:
          record.product_confirm = 0

    @api.depends('project_id')
    def _compute_product_set(self):
      for record in self:
        record.product_set = self.env['gvm.product'].search([('project_set','in',record.project_id.id),('issue','=',record.id)])

class GvmProjectProject(models.Model):
    _inherit = 'project.project'

    product = fields.One2many('gvm.product', 'project_ids',string='product')
    product_cost = fields.Float('자재비용', compute='_compute_product_cost', store=True)

    @api.depends('name')
    def _compute_percent(self):
        return
      #for record in self:
        #cal = self.env['gvm.product'].search([('project_set','in',record.id)])
        #total = len(cal)
        #a = 0
        #for c in cal:
        #  if c.destination_date:
        #    a += 1
        #if cal:
        #  record.percent = float(a)/float(total)*100

    @api.depends('product')
    def _compute_product_cost(self):
      _logger.warning('compute product cost')
      for record in self:
        total_product_cost = 0
        for pd in record.product:
          total_product_cost += pd.total_price
        record.product_cost = total_product_cost
