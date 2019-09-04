# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import datetime

from odoo import api, fields, models
from odoo import tools, _
from odoo.exceptions import ValidationError
from odoo.modules.module import get_module_resource


_logger = logging.getLogger(__name__)


class EmployeeCategory(models.Model):

    _name = "hr.employee.category"
    _description = "Employee Category"

    name = fields.Char(string="Employee Tag", required=True)
    color = fields.Integer(string='Color Index')
    employee_ids = fields.Many2many('hr.employee', 'employee_category_rel', 'category_id', 'emp_id', string='Employees')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists !"),
    ]


class Job(models.Model):

    _name = "hr.job"
    _description = "Job Position"
    _inherit = ['mail.thread']

    name = fields.Char(string='Job Title', required=True, index=True, translate=True)
    expected_employees = fields.Integer(compute='_compute_employees', string='Total Forecasted Employees', store=True,
        help='Expected number of employees for this job position after new recruitment.')
    no_of_employee = fields.Integer(compute='_compute_employees', string="Current Number of Employees", store=True,
        help='Number of employees currently occupying this job position.')
    no_of_recruitment = fields.Integer(string='Expected New Employees', copy=False,
        help='Number of new employees you expect to recruit.', default=1)
    no_of_hired_employee = fields.Integer(string='Hired Employees', copy=False,
        help='Number of hired employees for this job position during recruitment phase.')
    employee_ids = fields.One2many('hr.employee', 'job_id', string='Employees', groups='base.group_user')
    description = fields.Text(string='Job Description')
    requirements = fields.Text('Requirements')
    department_id = fields.Many2one('hr.department', string='Department')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    state = fields.Selection([
        ('recruit', 'Recruitment in Progress'),
        ('open', 'Not Recruiting')
    ], string='Status', readonly=True, required=True, track_visibility='always', copy=False, default='recruit', help="Set whether the recruitment process is open or closed for this job position.")
    timeattendance = fields.One2many('hr.timeattendance','name','근태기록')

    _sql_constraints = [
        ('name_company_uniq', 'unique(name, company_id, department_id)', 'The name of the job position must be unique per department in company!'),
    ]

    @api.depends('no_of_recruitment', 'employee_ids.job_id', 'employee_ids.active')
    def _compute_employees(self):
        employee_data = self.env['hr.employee'].read_group([('job_id', 'in', self.ids)], ['job_id'], ['job_id'])
        result = dict((data['job_id'][0], data['job_id_count']) for data in employee_data)
        for job in self:
            job.no_of_employee = result.get(job.id, 0)
            job.expected_employees = result.get(job.id, 0) + job.no_of_recruitment

    @api.model
    def create(self, values):
        """ We don't want the current user to be follower of all created job """
        return super(Job, self.with_context(mail_create_nosubscribe=True)).create(values)

    @api.multi
    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        if 'name' not in default:
            default['name'] = _("%s (copy)") % (self.name)
        return super(Job, self).copy(default=default)

    @api.multi
    def set_recruit(self):
        for record in self:
            no_of_recruitment = 1 if record.no_of_recruitment == 0 else record.no_of_recruitment
            record.write({'state': 'recruit', 'no_of_recruitment': no_of_recruitment})
        return True

    @api.multi
    def set_open(self):
        return self.write({
            'state': 'open',
            'no_of_recruitment': 0,
            'no_of_hired_employee': 0
        })


class Employee(models.Model):

    _name = "hr.employee"
    _description = "Employee"
    _order = 'name_related'
    _inherits = {'resource.resource': "resource_id"}
    _inherit = ['mail.thread']

    _mail_post_access = 'read'

    @api.model
    def _default_image(self):
        image_path = get_module_resource('hr', 'static/src/img', 'default_image.png')
        return tools.image_resize_image_big(open(image_path, 'rb').read().encode('base64'))

    # we need a related field in order to be able to sort the employee by name
    name_related = fields.Char(related='resource_id.name', string="Resource Name", readonly=True, store=True)
    country_id = fields.Many2one('res.country', string='Nationality (Country)')
    birthday = fields.Date('Date of Birth', groups='hr.group_hr_user')
    ssnid = fields.Char('SSN No', help='Social Security Number', groups='hr.group_hr_user')
    sinid = fields.Char('SIN No', help='Social Insurance Number', groups='hr.group_hr_user')
    identification_id = fields.Char(string='Identification No', groups='hr.group_hr_user')
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], groups='hr.group_hr_user')
    marital = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('widower', 'Widower'),
        ('divorced', 'Divorced')
    ], string='Marital Status', groups='hr.group_hr_user')
    department_id = fields.Many2one('hr.department', string='Department')
    address_id = fields.Many2one('res.partner', string='Working Address')
    address_home_id = fields.Many2one('res.partner', string='Home Address')
    bank_account_id = fields.Many2one('res.partner.bank', string='Bank Account Number',
        domain="[('partner_id', '=', address_home_id)]", help='Employee bank salary account', groups='hr.group_hr_user')
    work_phone = fields.Char('Work Phone')
    mobile_phone = fields.Char('Work Mobile')
    work_email = fields.Char('Work Email')
    work_location = fields.Char('Work Location')
    notes = fields.Text('Notes')
    parent_id = fields.Many2one('hr.employee', string='Manager')
    category_ids = fields.Many2many('hr.employee.category', 'employee_category_rel', 'emp_id', 'category_id', string='Tags')
    child_ids = fields.One2many('hr.employee', 'parent_id', string='Subordinates')
    resource_id = fields.Many2one('resource.resource', string='Resource',
        ondelete='cascade', required=True, auto_join=True)
    coach_id = fields.Many2one('hr.employee', string='Coach')
    job_id = fields.Many2one('hr.job', string='Job Title')
    passport_id = fields.Char('Passport No', groups='hr.group_hr_user')
    color = fields.Integer('Color Index', default=0)
    city = fields.Char(related='address_id.city')
    login = fields.Char(related='user_id.login', readonly=True)
    last_login = fields.Datetime(related='user_id.login_date', string='Latest Connection', readonly=True)
    holiday_count = fields.Float('남은연차', default=0.0)
    join_date = fields.Date('join_date')
    holiday_max_count = fields.Integer('연차총개수')

    # image: all image fields are base64 encoded and PIL-supported
    image = fields.Binary("Photo", default=_default_image, attachment=True,
        help="This field holds the image used as photo for the employee, limited to 1024x1024px.")
    image_medium = fields.Binary("Medium-sized photo", attachment=True,
        help="Medium-sized photo of the employee. It is automatically "
             "resized as a 128x128px image, with aspect ratio preserved. "
             "Use this field in form views or some kanban views.")
    image_small = fields.Binary("Small-sized photo", attachment=True,
        help="Small-sized photo of the employee. It is automatically "
             "resized as a 64x64px image, with aspect ratio preserved. "
             "Use this field anywhere a small image is required.")

    @api.constrains('parent_id')
    def _check_parent_id(self):
        for employee in self:
            if not employee._check_recursion():
               raise ValidationError(_('Error! You cannot create recursive hierarchy of Employee(s).'))

     #sh
    def _check_holiday_count(self):
      _logger.warning("test")

      #입사일기준
      employees = self.env['hr.employee'].search([])
      companyDate = ""
      for record in employees:
       fmt = '%Y-%m-%d'
       if record.join_date:
        companyDate = datetime.datetime.strptime(record.join_date,fmt).date()
      
      companyYear = companyDate.year
      companyMonth = companyDate.month
      companyDay = companyDate.day

      #현재시간
      now = datetime.datetime.now()
      presentYear = now.year
      presentMonth = now.month
      presentDay = now.day

      #3년이상 종사자
      year_entering = presentYear - companyYear
      year_check = year_entering % 2.0

      for record in employees:
       #1년미만 입사자
       if companyYear == presentYear and companyMonth != presentMonth and companyDay == presentDay:
        #연차 1개를 증가시킨다.
        record.holiday_count += 1.0
       #1년
       elif companyYear != presentYear and companyMonth == presentMonth and companyDay == presentDay:
        #2년이상 입사자 해당
        if (presentYear - companyYear) >= 2.0:
         #남은 연차의 갯수가 + 일경우 연차 초기화
         if record.holiday_count > 0.0:
          record.holiday_count = 0.0

        #연차 15개를 증가시킨다.
        record.holiday_count += 15.0
            
       #3년이상 재직 시 2년마다 연차 총 개수 1개씩 증가
       if year_entering > 2.0 and companyMonth == presentMonth and companyDay == presentDay:   
        #짝수
	if year_check == 0.0:
	 year_1count = (year_entering / 2.0) - 1.0
         record.holiday_count += year_1count
	#홀수
	else:
 	 year_2count = (year_entering - 1.0) / 2.0
	 record.holiday_count += year_2count
	
       #1년미만 입사자는 max_count = 0 
       if companyYear == presentYear and companyMonth != presentMonth and companyDay == presentDay:
        record.holiday_max_count = 0
       else:
        record.holiday_max_count = record.holiday_count

      _logger.warning(record.name)
      _logger.warning("Check Holiday Complete")


    @api.onchange('address_id')
    def _onchange_address(self):
        self.work_phone = self.address_id.phone
        self.mobile_phone = self.address_id.mobile

    @api.onchange('company_id')
    def _onchange_company(self):
        address = self.company_id.partner_id.address_get(['default'])
        self.address_id = address['default'] if address else False

    @api.onchange('department_id')
    def _onchange_department(self):
        self.parent_id = self.department_id.manager_id

    @api.onchange('user_id')
    def _onchange_user(self):
        self.work_email = self.user_id.email    
        self.name = self.user_id.name
        self.image = self.user_id.image

    @api.model
    def create(self, vals):
        tools.image_resize_images(vals)
        return super(Employee, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'address_home_id' in vals:
            account_id = vals.get('bank_account_id') or self.bank_account_id.id
            if account_id:
                self.env['res.partner.bank'].browse(account_id).partner_id = vals['address_home_id']
        tools.image_resize_images(vals)
        return super(Employee, self).write(vals)

    @api.multi
    def unlink(self):
        resources = self.mapped('resource_id')
        super(Employee, self).unlink()
        return resources.unlink()

    @api.multi
    def action_follow(self):
        """ Wrapper because message_subscribe_users take a user_ids=None
            that receive the context without the wrapper.
        """
        return self.message_subscribe_users()

    @api.multi
    def action_unfollow(self):
        """ Wrapper because message_unsubscribe_users take a user_ids=None
            that receive the context without the wrapper.
        """
        return self.message_unsubscribe_users()

    @api.model
    def _message_get_auto_subscribe_fields(self, updated_fields, auto_follow_fields=None):
        """ Overwrite of the original method to always follow user_id field,
            even when not track_visibility so that a user will follow it's employee
        """
        if auto_follow_fields is None:
            auto_follow_fields = ['user_id']
        user_field_lst = []
        for name, field in self._fields.items():
            if name in auto_follow_fields and name in updated_fields and field.comodel_name == 'res.users':
                user_field_lst.append(name)
        return user_field_lst

    @api.multi
    def _message_auto_subscribe_notify(self, partner_ids):
        # Do not notify user it has been marked as follower of its employee.
        return

class Department(models.Model):

    _name = "hr.department"
    _description = "Hr Department"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _order = "name"

    name = fields.Char('Department Name', required=True)
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)
    parent_id = fields.Many2one('hr.department', string='Parent Department', index=True)
    child_ids = fields.One2many('hr.department', 'parent_id', string='Child Departments')
    manager_id = fields.Many2one('hr.employee', string='Manager', track_visibility='onchange')
    member_ids = fields.One2many('hr.employee', 'department_id', string='Members', readonly=True)
    jobs_ids = fields.One2many('hr.job', 'department_id', string='Jobs')
    note = fields.Text('Note')
    color = fields.Integer('Color Index')

    @api.constrains('parent_id')
    def _check_parent_id(self):
        if not self._check_recursion():
            raise ValidationError(_('Error! You cannot create recursive departments.'))

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = record.name
            if record.parent_id:
                name = "%s / %s" % (record.parent_id.name_get()[0][1], name)
            result.append((record.id, name))
        return result

    @api.model
    def create(self, vals):
        # TDE note: auto-subscription of manager done by hand, because currently
        # the tracking allows to track+subscribe fields linked to a res.user record
        # An update of the limited behavior should come, but not currently done.
        department = super(Department, self.with_context(mail_create_nosubscribe=True)).create(vals)
        manager = self.env['hr.employee'].browse(vals.get("manager_id"))
        if manager.user_id:
            department.message_subscribe_users(user_ids=manager.user_id.ids)
        return department

    @api.multi
    def write(self, vals):
        """ If updating manager of a department, we need to update all the employees
            of department hierarchy, and subscribe the new manager.
        """
        # TDE note: auto-subscription of manager done by hand, because currently
        # the tracking allows to track+subscribe fields linked to a res.user record
        # An update of the limited behavior should come, but not currently done.
        if 'manager_id' in vals:
            manager_id = vals.get("manager_id")
            if manager_id:
                manager = self.env['hr.employee'].browse(manager_id)
                # subscribe the manager user
                if manager.user_id:
                    self.message_subscribe_users(user_ids=manager.user_id.ids)
            employees = self.env['hr.employee']
            for department in self:
                employees = employees | self.env['hr.employee'].search([
                    ('id', '!=', manager_id),
                    ('department_id', '=', department.id),
                    ('parent_id', '=', department.manager_id.id)
                ])
            employees.write({'parent_id': manager_id})
        return super(Department, self).write(vals)

class TimeAttendance(models.Model):

    _name = "hr.timeattendance"
    _description = "Hr Time Attendance"
    _order = "date desc"

    name = fields.Many2one('hr.employee','name')
    date = fields.Date('Date')
    gotowork = fields.Datetime('출근')
    gotohome = fields.Datetime('퇴근')
    weekend = fields.Boolean('weekend',compute='_compute_weekend')

    @api.depends('date')
    def _compute_weekend(self):
        for record in self:
           fmt = '%Y-%m-%d'
           d1 = datetime.datetime.strptime(record.date,fmt)
	   if d1.weekday() > 4:
	     record.weekend = True

    @api.model
    def parseSecom(self):
      td = datetime.timedelta(days=1)
      th = datetime.timedelta(hours=9)
      today = datetime.datetime.now() + th
      filename = today.strftime('%Y%m%d')
      f = open('/samba/GVM_'+filename+'.txt')
      #f = open('/samba/gvm_20180519.txt')
      _logger.warning(filename)

      readf = f.read()
      splitf = readf.split('\n')
      for lines in splitf:
        if lines:
          line = lines.split(',')
	  name = self.env['hr.employee'].search([('name','=',line[2].decode('EUC-KR').encode('UTF-8'))],limit=1).id
	  time = datetime.datetime.strptime(line[0] + " " + line[1],'%Y%m%d %H%M%S')
	  date = time.date()

	  record = self.env['hr.timeattendance'].search([('name','=',name),('date','=',date)],limit=1)
	  if not record:
            record = self.env['hr.timeattendance'].create({'name':name, 'date':date})

	  if line[3] == '1\r':
	    if record.gotowork:
	      continue
	    record.gotowork = time - th
	  if line[3] == '4\r':
	    if time.hour < 8: # 8시 이전 퇴근은 야근이다
	      date = (time - td).date()
	      record = self.env['hr.timeattendance'].search([('name','=',name),('date','=',date)],limit=1)
	      if not record:
                record = self.env['hr.timeattendance'].create({'name':name, 'date':date})
	    record.gotohome = time - th
      _logger.info('Parse Complite')
