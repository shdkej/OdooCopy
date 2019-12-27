# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api,fields, models
import logging

_logger = logging.getLogger(__name__)

class GvmProjectSign(models.Model):
    _inherit = 'project.project'

    sign = fields.One2many('gvm.signcontent','project','sign')
    user_cost = fields.Float('비용정산', compute='_compute_user_cost', store=True)

    @api.depends('sign')
    def _compute_user_cost(self):
      for record in self:
        total_sign_cost = 0
        for sign in record.sign:
          total_sign_cost += sign.finally_cost
        record.user_cost = total_sign_cost
