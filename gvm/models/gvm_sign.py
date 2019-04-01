# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import smtplib
from email.mime.text import MIMEText
import time
import logging
from datetime import datetime
import datetime as dt
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.tools.translate import _
from odoo.tools.sql import drop_view_if_exists
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import xlwt
import os
from cStringIO import StringIO

from bs4 import BeautifulSoup
from selenium import webdriver
import re
from odoo.http import request


_logger = logging.getLogger(__name__)

class GvmSign(models.Model):
    _name = "gvm.sign"
    _description = "sign"
    _order = 'num'

    name = fields.Char(string='sign',required=True)
    num = fields.Integer(string='number')

class GvmSignContent(models.Model):
    _name = "gvm.signcontent"
    _description = "signcontent"
    _order = 'create_date desc, name desc'

    user_id = fields.Many2one('res.users', string='user_id', default=lambda self: self.env.uid,store=True)
    name = fields.Char(string='name', default='New')
    color = fields.Integer('Color')
    sign_ids = fields.Integer('sign_ids',compute='_compute_sign')
    dep_ids = fields.Many2one('hr.department',string='department',compute='_compute_sign',store=True)
    job_ids = fields.Many2one('hr.job',string='job_id',compute='_compute_sign',store=True)

    writer = fields.Char(string='writer', compute='_compute_user_info')
    user_department = fields.Many2one('hr.department',string='user_department',compute='_compute_user_info')
    user_job_id = fields.Many2one('hr.job',string='user_job_id',compute='_compute_user_info')
    content = fields.Text(string='content',store=True)
    content2 = fields.Text(string='content',store=True)

    check = fields.Boolean(string='check',compute='_compute_check')
    request_check1 = fields.Many2one('hr.employee',string='request_check1',store=True)
    request_check2 = fields.Many2one('hr.employee',string='request_check2',store=True)
    request_check3 = fields.Many2one('hr.employee',string='request_check3',store=True)
    request_check4 = fields.Many2one('hr.employee',string='request_check4',store=True)
    request_check5 = fields.Many2one('hr.employee',string='request_check5',store=True)
    request_check6 = fields.Many2one('hr.employee',string='request_check6',store=True)
    check1 = fields.Many2one('res.users',string='check1',store=True)
    check2 = fields.Many2one('res.users',string='check2',store=True)
    check3 = fields.Many2one('res.users',string='check3',store=True)
    check4 = fields.Many2one('res.users',string='check4',store=True)
    check5 = fields.Many2one('res.users',string='check5',store=True)
    check6 = fields.Many2one('res.users',string='check6',store=True)
    check1_date = fields.Datetime('check1_date')
    check2_date = fields.Datetime('check2_date')
    check3_date = fields.Datetime('check3_date')
    check4_date = fields.Datetime('check4_date')
    check5_date = fields.Datetime('check5_date')
    check6_date = fields.Datetime('check6_date')
    reference = fields.Many2many('hr.employee',string='참조')

    my_doc_count = fields.Integer('my_doc', compute='_compute_my_check_count')
    my_check_count = fields.Integer('my_check', compute='_compute_my_check_count')
    my_ref_count = fields.Integer('my_ref', compute='_compute_my_check_count')
    create_date = fields.Date('create_date',default=fields.Datetime.now)
    date_from = fields.Date('start',required=True)
    date_to = fields.Date('end')
    project = fields.Many2one('project.project',string='name')
    sign = fields.Many2one('gvm.sign', string='sign',required=True)
    cost = fields.One2many('gvm.signcontent.cost','sign', string='cost')
    cost2 = fields.One2many('gvm.signcontent.cost2','sign', string='cost2')
    work = fields.One2many('gvm.signcontent.work','sign', string='work')
    timesheet = fields.Many2many('account.analytic.line','sign','timesheet',domain="[('user_id','=',uid)]",store=True,compute='_onchange_timesheet')
    reason = fields.Text('reason')
    rest1 = fields.Selection([('day','연차'),
      ('half','반차'),
      ('quarter','반반차'),
      ('vacation','휴가'),
      ('refresh','리프레시 휴가'),
      ('publicvacation','공가(예비군 등)'),
      ('sick','병가'),
      ('special','출산/특별휴가'),
      ('etc','기타')])
    basic_cost = fields.Integer('basic_cost',compute='_compute_basic_cost')
    had_cost = fields.Integer('had_cost')
    finally_cost = fields.Integer('finally_cost',compute='_compute_finally_cost')
    currency_yuan = fields.Float(string='yuan',default=171.73)
    currency_dong = fields.Float(string='dong',default=0.05)
    currency_dollar = fields.Float(string='dollar',default=1079.5)
    attachment = fields.Many2many('ir.attachment', domain="[('res_model','=','gvm.signcontent')]", string='도면')
    relate_sign = fields.Many2one('gvm.signcontent','sign')
    sign_line = fields.One2many('gvm.signcontent.line','sign','sign_line')

    check_all = fields.Boolean('전결')
    next_check = fields.Char(string='next_check',compute='_compute_next_check',store=True)
    state = fields.Selection([
        ('temp', '임시저장'),
        ('write', '상신'),
        ('check1', '검토'),
        ('check2', '결재'),
        ('check3', '결재'),
        ('check4', '결재'),
        ('check5', '결재'),
        ('done', '결재완료'),
        ('cancel', '반려')
        ], string='Status', readonly=True, index=True, copy=False, default='temp', track_visibility='onchange')
    holiday_count = fields.Char('holiday_count', compute='_compute_holiday_count')
    
    @api.depends('date_from','date_to','job_ids')
    def _compute_basic_cost(self):
        for record in self:
         if record.date_to and record.date_from:
           fmt = '%Y-%m-%d'
           d1 = datetime.strptime(record.date_to,fmt)
           d2 = datetime.strptime(record.date_from,fmt)
           dayDiff = str((d1-d2).days+1)
           job_id = record.job_ids.no_of_hired_employee
           record.basic_cost = int(dayDiff) * 8000
	   
    @api.depends('basic_cost','had_cost','cost')
    def _compute_finally_cost(self):
        for record in self:
         user_cost = 0
         if record.cost:
          for scost in record.cost:
           if scost.card == 'personal':
            calcost = scost.cost
            if scost.currency == 'dong':
              calcost = scost.cost * record.currency_dong
            elif scost.currency == 'yuan':
              calcost = scost.cost * record.currency_yuan
            elif scost.currency == 'dollar':
              calcost = scost.cost * record.currency_dollar
            user_cost += calcost
         final_cost = round((record.had_cost - record.basic_cost - user_cost +5)/100)*100
         record.finally_cost = final_cost

    def kb_parse(self,get_currency,get_date):
      driver = webdriver.PhantomJS(executable_path="/usr/phantomjs-2.1.1-linux-x86_64/bin/phantomjs",service_log_path='/usr/lib/python2.7/dist-packages/odoo/ghostdriver.log')
      url = 'https://okbfex.kbstar.com/quics?page=C015690#CP'
      driver.get(url)

      d1 = datetime.strptime(get_date,'%Y-%m-%d')
      date = str((d1 + dt.timedelta(days=1)).date())
      driver.execute_script("uf_yesterday('"+ date +"')")
      time.sleep(1)
      html = driver.page_source
      driver.quit()
      soup = BeautifulSoup(html,'lxml')
      list_p = soup.find('div',{'class':'btnTable'})

      currency_list = []
      for gc in get_currency:
       if list_p.select('a'):
        currency_list.append(re.sub('[^0-9.]','',list_p.select('a')[gc].parent.parent.select('td')[4].text))
       else:
        return self.kb_parse(get_currency,str((d1 - dt.timedelta(days=1)).date()))
      return currency_list

    @api.onchange('date_from')
    def _onchange_currency(self):
      if self.date_from and self.sign_ids == 3:
       set_currency = [0,9,36]
       currency_list = self.kb_parse(set_currency,self.date_from)
       self.currency_dollar = currency_list[0]
       self.currency_yuan = currency_list[1]
       self.currency_dong = float(currency_list[2])/100

    @api.depends('sign')
    def _compute_sign(self):
        for record in self:
           record.dep_ids = self.env['hr.employee'].search([('user_id','=',self.env.uid)]).department_id.id
           record.job_ids = self.env['hr.employee'].search([('user_id','=',self.env.uid)]).job_id.id
           record.sign_ids = record.sign.num
    @api.model
    def _compute_user_info(self):
        for record in self:
           record.user_job_id = self.env['hr.employee'].search([('user_id','=',self.env.uid)]).job_id.id
           record.user_department = self.env['hr.employee'].search([('user_id','=',self.env.uid)]).department_id.id
           record.writer = record.user_id.name
    @api.model
    def _compute_check(self):
        for record in self:
          if self._check_name() and self._check_me():
            record.check = True
    @api.depends('state')
    def _compute_next_check(self):
      index = ['request_check1','request_check2','request_check3','request_check4','request_check5','request_check6']
      for record in self:
        if record.state == 'cancel':
          record.next_check = record.writer
	  return False
        for i in index:
	  if record[i]:
            record.next_check = record[i].name
	    break

    @api.depends('user_id')
    def _compute_holiday_count(self):
      for record in self:
	hr_name = self.env['hr.employee'].search([('name','=',record.user_id.name)])
        record.holiday_count = hr_name.holiday_count

    @api.model
    def _compute_my_check_count(self):
      my_doc = self.env['gvm.signcontent'].search([('user_id','=',self.env.uid)])
      my_check_doc = self.env['gvm.signcontent'].search(['|','|','|','|','|',
                                     ('check1','=',self.env.uid),
                                     ('check2','=',self.env.uid),
                                     ('check3','=',self.env.uid),
                                     ('check4','=',self.env.uid),
                                     ('check5','=',self.env.uid),
                                     ('check6','=',self.env.uid)
				     ])
      my_check_finish_doc = self.env['gvm.signcontent'].search([('check1','=',self.env.uid)])
      my_check_deny_doc = self.env['gvm.signcontent'].search([('check1','=',self.env.uid)])
      my_ref_doc = self.env['gvm.signcontent'].search([('reference','=',self.env.uid)])
      for record in self:
        record.my_doc_count = len(my_doc)
        record.my_check_count = len(my_check_doc)
        record.my_ref_count = len(my_ref_doc)

    @api.onchange('sign_ids')
    def _default_check1(self):
        for record in self:
          user = self.env.uid
          dep = self.env['hr.department'].search([('member_ids.user_id','=',user)],limit=1)
          boss = dep.manager_id.id
          manager = self.env['hr.employee'].search([('department_id','=',10)])
          if record.sign_ids in [2,3,6]:
            record.request_check3 = boss
            record.request_check4 = manager[1].id
            record.request_check5 = manager[0].id
          elif record.sign_ids == 5:
            record.request_check3 = boss
            record.request_check4 = manager[2].id
            record.request_check5 = manager[0].id
	  #elif record.sign_ids == 1:
	  #  dep_list = []
	  #  dep_ids = self.env['hr.employee'].search([('department_id','=',dep.id)])
	  #  for dep_id in dep_ids:
	  #    dep_list.append(dep_id.id)
	  #  record.reference = dep_list
          else:
            record.request_check1 = False
            record.request_check2 = False
            record.request_check3 = boss
	    record.reference = False

    @api.depends('date_from','date_to')
    def _onchange_timesheet(self):
      for record in self:
        if record.sign_ids == 2:
         worktime = self.env['account.analytic.line'].search([('date_from','>=',record.date_from),('date_to','<=',record.date_to),('user_id','=',self.env.uid),('unit_amount','>=',1)])
         record.timesheet = worktime

    @api.model
    def _check_name(self):
        for record in self:
          if record.name != self.env.user.name and record.check1.id != self.env.uid and record.check2.id != self.env.uid and record.check3.id != self.env.uid and record.check4.id != self.env.uid and record.check5.id != self.env.uid and record.check6.id != self.env.uid:return True

    @api.model
    def _check_me(self):
        for record in self:
          if record.next_check == self.env.user.name :return True
    @api.model
    def _check_high_job_id(self):
        for record in self:
          if record.user_job_id.no_of_hired_employee >= 4 and record.job_ids.no_of_hired_employee < record.user_job_id.no_of_hired_employee:return True

    @api.multi
    def button_check_all(self):
        self.sudo(self.user_id.id).write({'state':'done', 'check3': self.env.uid, 'next_check':self.request_check4.id or 'done', 'check3_date': datetime.now()})
        return {}
    @api.multi
    def button_reorder(self):
        check1 = self.env['hr.employee'].search([('user_id','=',self.check1.id)],limit=1).id
        check2 = self.env['hr.employee'].search([('user_id','=',self.check2.id)],limit=1).id
        check3 = self.env['hr.employee'].search([('user_id','=',self.check3.id)],limit=1).id
        check4 = self.env['hr.employee'].search([('user_id','=',self.check4.id)],limit=1).id
        check5 = self.env['hr.employee'].search([('user_id','=',self.check5.id)],limit=1).id
        self.sudo(self.user_id.id).write({'state': 'write',
	                                  'check1':False,
					  'check2':False,
					  'check3':False,
					  'check4':False,
					  'check5':False,
					  'reason':False,
	                                  'check1_date':False,
	                                  'check2_date':False,
	                                  'check3_date':False,
	                                  'check4_date':False,
	                                  'check5_date':False,
					  'request_check1':check1 or self.request_check1.id,
					  'request_check2':check2 or self.request_check2.id,
					  'request_check3':check3 or self.request_check3.id,
					  'request_check4':check4 or self.request_check4.id,
					  'request_check5':check5 or self.request_check5.id,
					  'next_check':self.check1.name})
        return {}

    @api.multi
    def sign_view(self):
        uname = self.env['hr.employee'].search([('user_id','=',self.env.uid)]).id
        username = self.env['hr.employee'].search([('user_id','=',self.env.uid)]).name
        domain = ['|','&','|',('request_check1','=',uname),('request_check2','=',uname),('request_check3','=',uname),('next_check','=',username)]
        return {
            'name': _('Sign'),
            'domain': domain,
            'res_model': 'gvm.signcontent',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'limit': 80,
            'context': "{}"
        }

    @api.multi
    def sign_reference_view(self):
        uname = self.env['hr.employee'].search([('user_id','=',self.env.uid)]).id
        username = self.env['hr.employee'].search([('user_id','=',self.env.uid)]).name
        domain = [('reference','in',uname)]
        return {
            'name': _('Sign'),
            'domain': domain,
            'res_model': 'gvm.signcontent',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'limit': 80,
            'context': "{}"
        }

    @api.multi
    def button_confirm(self):
        self.gvm_send_mail(self, self.id)
	check_name = ''
	if self.request_check1:
	 check_name = self.request_check1.name
	elif self.request_check3:
	 check_name = self.request_check3.name
	self.write({'next_check':check_name,
	    	    'state':'write'
	})
	if self.sign.num == 1:
	  count = self.check_holiday_count()
	  hr_name = self.env['hr.employee'].sudo(1).search([('name','=',self.user_id.name)])
	  h_count = float(hr_name.holiday_count) - float(count)
	  if h_count < -7:
            raise UserError(_('사용 가능한 연차 개수를 초과하셨습니다.'))
	  hr_name.holiday_count = str(h_count)

    def check_holiday_count(self):
        count = 0
	if self.rest1 in ['refresh','publicvacation','special']:
	  return count
	if self.rest1 == 'half':
	  count = 0.5
	  return count
	elif self.rest1 == 'quarter':
	  count = 0.25
	  return count
        fmt = '%Y-%m-%d'
        d1 = datetime.strptime(self.date_to,fmt)
        d2 = datetime.strptime(self.date_from,fmt)
        count = (d1-d2).days+1
	return count

    def gvm_send_mail(self, vals, postId):
        dep = self.env['hr.department'].search([('member_ids.user_id','=',self.env.uid)]).id
#        same_dep = self.env['hr.employee'].search([('department_id','=',dep),('job_id.no_of_hired_employee','>',3)])
        check1 = vals.request_check1.id
        check2 = vals.request_check2.id
        check3 = vals.request_check3.id
        we = self.env['hr.employee'].search([('id','in',(check1,check2,check3))])

        post = '결재문서'
        sender = 'nohsh@gvmltd.com'
        receivers = []
#        for rc in same_dep:
#         receivers.append(str(rc.work_email))
        for person in we:
          receivers.append(str(person.work_email))
        receivers.append(sender)
        head = ['kangky@gvmltd.com','kimgt@gvmltd.com']
#        if dep != 3:
#          receivers.append(head)
       
        menu_id = "320"
        post_id = str(postId)
        #url = str(request.httprequest.url_root)
	url = "https://erp.gvmltd.com/"
        html = str('<a href="' + url + 
          'web#view_type=form&model=gvm.signcontent&menu_id=' + menu_id + 
          '" style="padding: 5px 10px; font-size: 12px; line-height: 18px; color: #FFFFFF; border-color:#875A7B; text-decoration: none; display: inline-block; margin-bottom: 0px; font-weight: 400; text-align: center; vertical-align: middle; cursor: pointer; white-space: nowrap; background-image: none; background-color: #875A7B; border: 1px solid #875A7B; border-radius:3px">바로가기</a>')

        msg = MIMEText(html, 'html', _charset='utf-8')
        name = self.env.user.name.encode('utf-8')
        msg['subject'] = "[GVM]"+ name +" 님이 " + post + " 를 상신했습니다."
        msg['from'] = 'GVM_ERP'
        s = smtplib.SMTP_SSL(host='smtp.mailplug.co.kr', port=465)
        s.login(user='nohsh@gvmltd.com', password='@shtjdgh412')
        s.sendmail(sender, receivers, msg.as_string())
#        if dep in [4,5,7]:
#          msg['subject'] = "[참고][GVM]"+ name +" 님이 " + post + " 를 상신했습니다."
#          s.sendmail(sender, head, msg.as_string())
#        s.sendmail(sender, sender, msg.as_string())
        s.quit()

    @api.model
    def create(self, vals):
        if vals.get('name','New') == 'New':
           vals['name'] = self.env['ir.sequence'].next_by_code('gvm.sign.number') or '/'
        res = super(GvmSignContent, self).create(vals)
	return res

    @api.multi
    def unlink(self):
        for record in self:
            if not record.user_id.name == self.env.user.name:
                raise UserError(_('본인 외 삭제 불가'))
        return super(GvmSignContent, self).unlink()

    @api.multi
    def write(self, vals):
        allower = [1,168,294]
        for record in self:
            if record.state in ['temp','write','cancel']:
	     if self.env.user.name != record.user_id.name and self.env.uid != 1:
               raise UserError(_('본인 외 수정 불가'))
            else:
             if self.env.uid not in allower:
                raise UserError(_('이미 결재가 진행 중인 문서는 수정이 불가합니다.'))
        return super(GvmSignContent, self).write(vals)


class GvmSignContentCost(models.Model):
    _name = "gvm.signcontent.cost"
    _description = "signcontent cost"
    _order = 'create_date, date'

    name = fields.Char(string='name',required=True)
    date = fields.Date(string='date')
    sign = fields.Many2one('gvm.signcontent','sign')
    cost = fields.Integer('cost')
    currency_id = fields.Many2one('res.currency',string='Currency')
    currency = fields.Selection([('won','원'),('dong','동'),('yuan','위안'),('dollar','달러'),('etc','기타')],default='won',string='화폐')
    description = fields.Char(string='description')
    ratio = fields.Float('환율',default='1')
    card = fields.Selection([('personal','개인'),('corporation','법인')],default='personal')

class GvmSignContentCost2(models.Model):
    _name = "gvm.signcontent.cost2"
    _description = "signcontent cost2"
    _order = 'create_date, date'

    name = fields.Char(string='name',required=True)
    date = fields.Date(string='date')
    sign = fields.Many2one('gvm.signcontent','sign')
    cost = fields.Integer('cost')
    currency_id = fields.Many2one('res.currency',string='Currency')
    currency = fields.Selection([('won','원'),('dong','동'),('yuan','위안'),('dollar','달러'),('etc','기타')],default='won',string='화폐')
    description = fields.Char(string='description')
    ratio = fields.Float('환율',default='1')
    card = fields.Selection([('personal','개인'),('corporation','법인')],default='personal')

class GvmSignContentWork(models.Model):
    _name = "gvm.signcontent.work"
    _description = "signcontent work"
    _order = 'create_date, date'

    name = fields.Char(string='name',required=True)
    date_from = fields.Date(string='datefrom')
    date_to = fields.Date(string='dateto')
    sign = fields.Many2one('gvm.signcontent','sign')
    timesheet = fields.Many2one('account.analytic.line','timesheet')
    
class GvmSignLine(models.Model):
    _name = "gvm.signcontent.line"
    _order = ''

    name = fields.Many2one('hr.employee',string='name')
    sequence = fields.Integer('순번')
    state = fields.Selection([('sign','결재'),('2','합의'),('3','참조'),('4','열람')])
    sign = fields.Many2one('gvm.signcontent','sign')

