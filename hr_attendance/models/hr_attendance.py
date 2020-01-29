# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime

from odoo import models, fields, api, exceptions, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

import logging

_logger = logging.getLogger(__name__)

class HrAttendance(models.Model):
    _name = "hr.attendance"
    _description = "Attendance"
    _order = "create_date desc"

    def _default_employee(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    employee_id = fields.Many2one('hr.employee', string="Employee", default=_default_employee, required=True, ondelete='cascade', index=True)
    department_id = fields.Many2one('hr.department', string="Department", related="employee_id.department_id")
    check_in = fields.Datetime(string="[출장] 출근")
    check_in_place = fields.Char('[출장] 출근장소')
    check_out = fields.Datetime(string="[출장] 퇴근")
    check_out_place = fields.Char('[출장] 퇴근장소')
    #worked_hours = fields.Float(string='Worked Hours', compute='_compute_worked_hours', store=True, readonly=True)
    worked_hours = fields.Float(string='Worked Hours', store=True, readonly=True)
    outing_start = fields.Datetime(string="[외근] 출발")
    outing_end = fields.Datetime(string="[외근] 퇴근")
    reason = fields.Char('[외근] 외근사유')
    destination = fields.Char('[외근] 목적지')
    date = fields.Char('[외근] 업무예정시간')
    outing_place = fields.Char('[외근] 퇴근장소')

    #@api.multi
    #def name_get(self):
    #    result = []
    #    for attendance in self:
    #        if not attendance.check_out:
    #          if not attendance.outing_start:
    #            result.append((attendance.id, _("%(empl_name)s from ") % {
    #                'empl_name': attendance.employee_id.name_related,
#                    'check_in': fields.Datetime.to_string(fields.Datetime.context_timestamp(attendance, fields.Datetime.from_string(attendance.check_in))),
    #            }))
    #        else:
    #          if not attendance.outing_end:
    #            result.append((attendance.id, _("%(empl_name)s from ") % {
    #                'empl_name': attendance.employee_id.name_related,
 #                   'check_in': fields.Datetime.to_string(fields.Datetime.context_timestamp(attendance, fields.Datetime.from_string(attendance.check_in))),
 #                   'check_out': fields.Datetime.to_string(fields.Datetime.context_timestamp(attendance, fields.Datetime.from_string(attendance.check_out))),
    #            }))
    #    return result

    @api.onchange('check_in', 'check_out')
    def _compute_checked(self):
        hr_employee = self.env['hr.employee'].search([('user_id','=',self.env.uid)])
        if self.check_in != False:
            hr_employee.write({'attendance_state':'checked_in'})
        elif self.check_out != False:
            hr_employee.write({'attendance_state':'checked_out'})

    @api.onchange('outing_in', 'outing_out')
    def _compute_outing(self):
        hr_employee = self.env['hr.employee'].search([('user_id','=',self.env.uid)])
        if self.outing_in != False:
            hr_employee.write({'outing_state':'outing_in'})
        elif self.outing_out != False:
            hr_employee.write({'outing_state':'outing_out'})

    #@api.depends('check_in', 'check_out')
    def _compute_worked_hours(self):
        for attendance in self:
            if attendance.check_out:
                delta = datetime.strptime(attendance.check_out, DEFAULT_SERVER_DATETIME_FORMAT) - datetime.strptime(
                    attendance.check_in, DEFAULT_SERVER_DATETIME_FORMAT)
                attendance.worked_hours = delta.total_seconds() / 3600.0

    @api.multi
    def unlink(self):       
        hr_employee = self.env['hr.employee'].search([('user_id','=',self.env.uid)])
        hr_employee.write({'outing_state':'outing_out',
                           'attendance_state':'checked_out',
        })

        return super(HrAttendance, self).unlink()

    #@api.constrains('check_in', 'check_out')
    def _check_validity_check_in_check_out(self):
        """ verifies if check_in is earlier than check_out. """
        for attendance in self:
            if attendance.check_in and attendance.check_out:
                if attendance.check_out < attendance.check_in:
                    raise exceptions.ValidationError(_('"Check Out" time cannot be earlier than "Check In" time.'))

    #@api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        """ Verifies the validity of the attendance record compared to the others from the same employee.
            For the same employee we must have :
                * maximum 1 "open" attendance record (without check_out)
                * no overlapping time slices with previous employee records
        """
        for attendance in self:
            # we take the latest attendance before our check_in time and check it doesn't overlap with ours
            last_attendance_before_check_in = self.env['hr.attendance'].search([
                ('employee_id', '=', attendance.employee_id.id),
                ('check_in', '<=', attendance.check_in),
                ('id', '!=', attendance.id),
            ], order='check_in desc', limit=1)
            if last_attendance_before_check_in and last_attendance_before_check_in.check_out and last_attendance_before_check_in.check_out > attendance.check_in:
                raise exceptions.ValidationError(_("Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s") % {
                    'empl_name': attendance.employee_id.name_related,
                    'datetime': fields.Datetime.to_string(fields.Datetime.context_timestamp(self, fields.Datetime.from_string(attendance.check_in))),
                })
            if not attendance.check_out:
                # if our attendance is "open" (no check_out), we verify there is no other "open" attendance
                no_check_out_attendances = self.env['hr.attendance'].search([
                    ('employee_id', '=', attendance.employee_id.id),
                    ('check_out', '=', False),
                    ('id', '!=', attendance.id),
                ])
                if no_check_out_attendances:
                    raise exceptions.ValidationError(_("Cannot create new attendance record for %(empl_name)s, the employee hasn't checked out since %(datetime)s") % {
                        'empl_name': attendance.employee_id.name_related,
                        'datetime': fields.Datetime.to_string(fields.Datetime.context_timestamp(self, fields.Datetime.from_string(no_check_out_attendances.check_in))),
                    })
            else:
                # we verify that the latest attendance with check_in time before our check_out time
                # is the same as the one before our check_in time computed before, otherwise it overlaps
                last_attendance_before_check_out = self.env['hr.attendance'].search([
                    ('employee_id', '=', attendance.employee_id.id),
                    ('check_in', '<', attendance.check_out),
                    ('id', '!=', attendance.id),
                ], order='check_in desc', limit=1)
		
                if last_attendance_before_check_out and last_attendance_before_check_in != last_attendance_before_check_out:
                    raise exceptions.ValidationError(_("Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s") % {
                        'empl_name': attendance.employee_id.name_related,
                        'datetime': fields.Datetime.to_string(fields.Datetime.context_timestamp(self, fields.Datetime.from_string(last_attendance_before_check_out.check_in))),
                    })

    @api.multi
    def copy(self):
        raise exceptions.UserError(_('You cannot duplicate an attendance.'))
