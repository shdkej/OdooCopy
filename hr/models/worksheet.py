# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class GvmWorkSheet(models.Model):

    _name = "gvm.worksheet"
    _description = "Work Sheet"

    name = fields.Text(string="work", required=True)
    date_start = fields.Datetime('시작시간')
    date_end = fields.Datetime('종료시간')
    part = fields.Many2one('project.task','part',store=True,copy=True)
    hr = fields.Many2one('hr.employee','hr')

class TaskInherit(models.Model):

    _inherit = 'project.task'

    worksheet = fields.One2many('gvm.worksheet','part','worksheet')
