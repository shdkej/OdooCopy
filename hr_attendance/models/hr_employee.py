# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from random import choice
from string import digits
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
from odoo import models, fields, api, exceptions, _, SUPERUSER_ID
from datetime import datetime
import requests
import logging
import sys

_logger = logging.getLogger(__name__)

class HrEmployee(models.Model):
    _inherit = "hr.employee"
    _description = "Employee"

    def _default_random_pin(self):
        return ("".join(choice(digits) for i in range(4)))

    def _default_random_barcode(self):
        barcode = None
        while not barcode or self.env['hr.employee'].search([('barcode', '=', barcode)]):
            barcode = "".join(choice(digits) for i in range(8))
        return barcode

    barcode = fields.Char(string="Badge ID", help="ID used for employee identification.", default=_default_random_barcode, copy=False)
    pin = fields.Char(string="PIN", default=_default_random_pin, help="PIN used to Check In/Out in Kiosk Mode (if enabled in Configuration).", copy=False)

    attendance_ids = fields.One2many('hr.attendance', 'employee_id', help='list of attendances for the employee')
    last_attendance_id = fields.Many2one('hr.attendance', compute='_compute_last_attendance_id')
    attendance_state = fields.Selection(string="Attendance", compute='_compute_attendance_state', selection=[('checked_out', "Checked out"), ('checked_in', "Checked in")])
    manual_attendance = fields.Boolean(string='Manual Attendance', compute='_compute_manual_attendance', inverse='_inverse_manual_attendance',
                                       help='The employee will have access to the "My Attendances" menu to check in and out from his session')
    check_today_attendance = fields.Boolean()
    _sql_constraints = [('barcode_uniq', 'unique (barcode)', "The Badge ID must be unique, this one is already assigned to another employee.")]

    @api.multi
    def _compute_manual_attendance(self):
        for employee in self:
            employee.manual_attendance = employee.user_id.has_group('hr.group_hr_attendance') if employee.user_id else False

    @api.multi
    def _inverse_manual_attendance(self):
        manual_attendance_group = self.env.ref('hr.group_hr_attendance')
        for employee in self:
            if employee.user_id:
                if employee.manual_attendance:
                    manual_attendance_group.users = [(4, employee.user_id.id, 0)]
                else:
                    manual_attendance_group.users = [(3, employee.user_id.id, 0)]

    @api.depends('attendance_ids')
    def _compute_last_attendance_id(self):
        for employee in self:
            employee.last_attendance_id = employee.attendance_ids and employee.attendance_ids[0] or False

    @api.depends('last_attendance_id.check_in', 'last_attendance_id.check_out', 'last_attendance_id')
    def _compute_attendance_state(self):
        for employee in self:
            employee.attendance_state = employee.last_attendance_id and not employee.last_attendance_id.check_out and 'checked_in' or 'checked_out'

    @api.constrains('pin')
    def _verify_pin(self):
        for employee in self:
            if employee.pin and not employee.pin.isdigit():
                raise exceptions.ValidationError(_("The PIN must be a sequence of digits."))

    @api.model
    def attendance_scan(self, barcode):
        """ Receive a barcode scanned from the Kiosk Mode and change the attendances of corresponding employee.
            Returns either an action or a warning.
        """
        employee = self.search([('barcode', '=', barcode)], limit=1)
        return employee and employee.attendance_action('hr_attendance.hr_attendance_action_kiosk_mode') or \
            {'warning': _('No employee corresponding to barcode %(barcode)s') % {'barcode': barcode}}

    @api.multi
    def attendance_manual(self, next_action, address, entered_pin=None):
        self.ensure_one()
        if not (entered_pin is None) or self.env['res.users'].browse(SUPERUSER_ID).has_group('hr_attendance.group_hr_attendance_use_pin') and (self.user_id and self.user_id.id != self._uid or not self.user_id):
            if entered_pin != self.pin:
                return {'warning': _('Wrong PIN')}
	
        return self.attendance_action(next_action, address)
    
    def _Check_check_out_time(self):
        """ 퇴근을 하지 않았을경우, 다음날 00시 00분 00초에 자동으로  퇴근이 된다."""
        date = datetime.now()
        hour = date.hour
        minute = date.minute
 	_logger.warning("test")

        check_out_time = datetime.now()
        check_out_time = check_out_time.replace(hour=15, minute=0,second=0)
						    
        hr_attendance = self.env['hr.attendance'].search([('check_out', '=', False)])
  	_logger.warning("test1")					         
        if hour == 15 and minute == 00:
         for att in hr_attendance:
	     _logger.warning("test2")
	     att.write({
		     'check_out':check_out_time
	     })

    @api.multi
    def attendance_action(self, next_action, location):
        """ Changes the attendance of the employee.
            Returns an action to the check in/out message,
            next_action defines which menu the check in/out message should return to. ("My Attendances" or "Kiosk Mode")
        """
        self.ensure_one()
        action_message = self.env.ref('hr_attendance.hr_attendance_action_greeting_message').read()[0]
        action_message['previous_attendance_change_date'] = self.last_attendance_id and (self.last_attendance_id.check_out or self.last_attendance_id.check_in) or False
        action_message['employee_name'] = self.name
        action_message['next_action'] = next_action

        if self.user_id:
            modified_attendance = self.sudo(self.user_id.id).attendance_action_change(location)
        else:
            modified_attendance = self.sudo().attendance_action_change()
        action_message['attendance'] = modified_attendance.read()[0]
        return {'action': action_message}
   
   #sh
    def _Check_check_out_time(self):
       """ 퇴근을 하지 않았을경우, 다음날 00시 00분 00초에 자동으로  퇴근이 된다."""
       #현재시간	
       date = datetime.now()
       #현재 시
       hour = date.hour
       #현재 분
       minute = date.minute
       
       #현재시간
       check_out_time = datetime.now()
       #00시 00분 00초 
       #한국과의 시차는9 시간
       check_out_time = check_out_time.replace(hour=15, minute=0,second=0)
       
       #체크아웃 정보 가져오기
       hr_attendance = self.env['hr.attendance'].search([('check_out', '=', False)])
      
       #체크아웃 시간이 00시 00분일때
       if hour == 15 and minute == 00:
        #체크아웃을 작성
	for att in hr_attendance:
           att.write({
	     'check_out':check_out_time
	   })
#        return self.env['hr.attendance'].write(check_out_date)

    @api.multi
    def attendance_action_change(self, location):
        """ Check In/Check Out action
            Check In: create a new attendance record
            Check Out: modify check_out field of appropriate attendance record
        """
        if len(self) > 1:
            raise exceptions.UserError(_('Cannot perform check in or check out on multiple employees.'))
	#sh
	#현재시간
	present_date = datetime.now()
	#해당 유저의 처음 출근 시간 파악
	hr_attendance = self.env['hr.attendance'].search([('employee_id', '=', self.id)], limit=1)
	check_in_date = hr_attendance.check_in
	#출퇴근 기준 시간의 초기화
	check_in_cut_line = ""
	check_out_cut_line = ""
	
	#해당 유저의 처음 출근시간이 존재할 경우
	if check_in_date != False :
	 #해당 유저의 첫 체크인시간을 년,월,일,시간,분,초로 변경
	 check_in_last_time = datetime.strptime(check_in_date, '%Y-%m-%d %H:%M:%S')
	 #체크인 기준시간(다음날 00시 00분 00초)
	 #15시간을 더해준 이유: 서버의 시간은 미국시간이므로 한국과 9시간의 차이가 발생함
	 check_in_cut_line = check_in_last_time
	 check_in_cut_line = check_in_cut_line.replace(hour=15, minute=0,second=0)
	 #체크아웃 기준시간(1시간뒤)
	 check_out_cut_line = check_in_last_time + relativedelta(hours=1)

	#체크인상태일 경우
	if self.attendance_state != 'checked_in':
	     #해당 유저의 출근시간이 존재할경우
	     if check_in_date != False:
	       #출퇴근 기준시간보다 현재의 시간이 클 경우
	       if present_date > check_in_cut_line:
	         #서버에 입력
	         vals = {
                    'employee_id': self.id,
                    'check_in': present_date,
                    'check_in_place': location,
                 }
	         return self.env['hr.attendance'].create(vals)
	       #출퇴근 기준시간보다 현재의 시간이 작을 경우 
	       else:
	         raise UserError(_('출근시간이 아닙니다.'))
	     #해당 유저의 출퇴근시간이 존재하지 않을경우 
	     else:
	       #서버에 생성
	       vals = {
	         'employee_id': self.id,
	         'check_in': present_date,
                 'check_in_place': location,
	       }
               return self.env['hr.attendance'].create(vals)
	#체크아웃상태일 경우       
        else:
	   #해당 유저의 체크아웃 파악
           attendance = self.env['hr.attendance'].search([('employee_id', '=', self.id), ('check_out', '=', False)], limit=1)       
	   if attendance:
	    #출퇴근 기준시간 보다 현재의 시간이 클경우
     	    if present_date > check_out_cut_line:
	      #서버에 생성
              attendance.check_out = present_date
	      attendance.check_out_place = location
	    #출퇴근 기준시간 보다 현쟈시간이 작을경우
	    else:
	      raise UserError(_('퇴근시간이 아닙니다.'))
           return attendance

    @api.model_cr_context
    def _init_column(self, column_name):
        """ Initialize the value of the given column for existing rows.
            Overridden here because we need to have different default values
            for barcode and pin for every employee.
        """
        if column_name not in ["barcode", "pin"]:
            super(HrEmployee, self)._init_column(column_name)
        else:
            default_compute = self._fields[column_name].default

            query = 'SELECT id FROM "%s" WHERE "%s" is NULL' % (
                self._table, column_name)
            self.env.cr.execute(query)
            employee_ids = self.env.cr.fetchall()

            for employee_id in employee_ids:
                default_value = default_compute(self)

                query = 'UPDATE "%s" SET "%s"=%%s WHERE id = %s' % (
                    self._table, column_name, employee_id[0])
                self.env.cr.execute(query, (default_value,))

    def google_geocode(self, location):
        url = 'https://maps.googleapis.com/maps/api/geocode/json?key=AIzaSyB99SRIPe6V5HCvbhf9rzaEbi8E2jP_1Zg&latlng=' + str(location[0]) + ',' + str(location[1])
        r = requests.get(url).json()
        address = r['plus_code']['compound_code']
	global_address = address
        return address

    def naver_geocode(self, location):
        reload(sys)
        sys.setdefaultencoding('utf-8')
	url = 'https://naveropenapi.apigw.ntruss.com/map-reversegeocode/v2/gc?coords=' + str(location[1]) + ',' + str(location[0]) + '&output=json&orders=legalcode,roadaddr'
	headers = {
	  'X-NCP-APIGW-API-KEY-ID':'39295gvivi',
	  'X-NCP-APIGW-API-KEY':'vmc51DB35kxwYIW8BivXpZwMhJTKMKzYm9VUcHoP'
	}
	r = requests.get(url, headers=headers).json()
	address = r
        full_address = ''
        address = r
        status = address['status']['name']
	_logger.warning(status)
        if status == 'ok':
          name4 = str(address['results'][0]['region']['area4']['name'])
          name3 = str(address['results'][0]['region']['area3']['name'])
          name2 = str(address['results'][0]['region']['area2']['name'])
          name1 = str(address['results'][0]['region']['area1']['name'])
          name0 = str(address['results'][0]['region']['area0']['name'])
	  _logger.warning(name0)

          roadaddr0, roadaddr1 = '',''
	  if len(address['results']) > 1:
            roadaddr0 = str(address['results'][1]['land']['name'])
            roadaddr1 = str(address['results'][1]['land']['number1'])

          full_address = name1 + name2 + name3 + name4 + roadaddr0 + roadaddr1
	else:
	  full_address = self.google_geocode(location)


        return full_address

    def geolocation(self):
        url = 'https://www.googleapis.com/geolocation/v1/geolocate?key=AIzaSyB99SRIPe6V5HCvbhf9rzaEbi8E2jP_1Zg'
        r = requests.post(url).json()
	_logger.warning(r)
        lat = str(r['location']['lat'])
        lng = str(r['location']['lng'])
        latlng = [lat,lng]

        return latlng













































