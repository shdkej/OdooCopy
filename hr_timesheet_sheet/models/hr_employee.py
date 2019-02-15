# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    _description = 'Employee'

    timesheet_count = fields.Integer(compute='_compute_timesheet_count', string='Timesheets')
    timesheet_ids = fields.One2many('account.analytic.line','employee','timesheet',compute='_compute_worksheet')
    wproject = fields.Char('프로젝트',compute='_compute_project',store=True)

    @api.multi
    def _compute_timesheet_count(self):
        for employee in self:
            employee.timesheet_count = employee.env['hr_timesheet_sheet.sheet'].search_count([('employee_id', '=', employee.id)])

    @api.depends('user_id')
    def _compute_worksheet(self):
      for record in self:
        line = self.env['account.analytic.line'].search([('user_id','=',record.user_id.id)],limit=10)
        record.timesheet_ids = line

    @api.depends('timesheet_ids')
    def _compute_project(self):
      for record in self:
        if record.timesheet_ids:
	  project_name = self.env['project.project'].search([('id','=',record.timesheet_ids[0].project_id.id)],limit=1).name
          record.wproject = project_name
