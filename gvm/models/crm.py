# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api,fields, models
import logging

_logger = logging.getLogger(__name__)

class GvmCrmSign(models.Model):
    _inherit = 'crm.lead'

