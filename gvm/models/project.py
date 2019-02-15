# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api,fields, models
import logging

_logger = logging.getLogger(__name__)

class GvmProjectSign(models.Model):
    _inherit = 'project.project'

    sign = fields.One2many('gvm.signcontent','project','sign')
