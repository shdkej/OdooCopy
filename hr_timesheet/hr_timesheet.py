# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)
class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    task_id = fields.Many2one('project.task', 'Task')
    project_id = fields.Many2one('project.project', 'Project', domain=[('allow_timesheets', '=', True)])
    world = fields.Selection([('in','국내'),('out','해외')])
    department_id = fields.Many2one('hr.department', "Department", related='user_id.employee_ids.department_id', store=True, readonly=True)

    @api.onchange('project_id')
    def onchange_project_id(self):
        self.task_id = False
        if self.project_id.world:
          self.world = 'out'
        else:
          self.world = 'in'

    @api.onchange('date')
    def onchange_date(self):
      name = self.env['hr.employee'].search([('user_id','=',self.env.uid)]).id
      secom = self.env['hr.timeattendance'].search([('name','=',name),('date','=',self.date)])
      if secom:
        self.date_from = secom.gotowork
        self.date_to = secom.gotohome

#    @api.model
#    def create(self, vals):
#       if vals.get('project_id'):
#          project = self.env['project.project'].browse(vals.get('project_id'))
#          vals['account_id'] = project.analytic_account_id.id
#       res = super(AccountAnalyticLine, self).create(vals)
       #check = self.env['project.task'].search([('overlap','=',res.name),('project_id','=',res.project_id.id)])
       #if check:
       #  _logger.warning(check)
#       return res

    @api.multi
    def write(self, vals):
        if vals.get('project_id'):
            project = self.env['project.project'].browse(vals.get('project_id'))
            vals['account_id'] = project.analytic_account_id.id
        for record in self:
	     if self.env.user.name != record.user_id.name and self.env.uid != 1:
               raise UserError(_('본인 외 수정 불가'))
        return super(AccountAnalyticLine, self).write(vals)

