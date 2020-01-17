#/ -*- coding: utf-8 -*-
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
import sys
abspath = sys.path.append(os.path.abspath('gvm/models'))
from sendmail import gvm_mail

_logger = logging.getLogger(__name__)

class GvmSign(models.Model):
    _name = "gvm.sign"
    _description = "sign"
    _order = 'sign_sequence'

    @api.model
    def default_sequence(self):
        return  self.env['ir.sequence'].next_by_code('sign.number')
    
    sign_sequence = fields.Integer (' 순번 ', default=default_sequence)
    name = fields.Char(string='sign',required=True)
    num = fields.Integer(string='number')

class GvmSignContent(models.Model):
    _name = "gvm.signcontent"
    _description = "signcontent"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _order = 'create_date desc, name desc'

    user_id = fields.Many2one('res.users', string='user_id', default=lambda self: self.env.uid,store=True)
    name = fields.Char(string='name', default='New')
    color = fields.Integer('Color')
    sign_ids = fields.Integer('sign_ids',compute='_compute_sign',store=True)
    dep_ids = fields.Many2one('hr.department',string='department',compute='_compute_sign',store=True)
    job_ids = fields.Many2one('hr.job',string='job_id',compute='_compute_sign',store=True)

    writer = fields.Char(string='writer', compute='_compute_user_info')
    user_department = fields.Many2one('hr.department',string='user_department',compute='_compute_user_info')
    user_job_id = fields.Many2one('hr.job',string='user_job_id',compute='_compute_user_info')
    content = fields.Text(string='내용',store=True)
    content2 = fields.Text(string='출장목적',store=True)
    content3 = fields.Text(string='비고',store=True)
    
    #메일을보냈는지확인
    check_mail = fields.Boolean(default=False)
    #출장비완료보고서 확인 후 출장비정산서 작성가능 
    check_confirm = fields.Boolean('상신확인', default=False)
    #참조문서
    reference = fields.Many2many('hr.employee',string='참조')
    #결재자 유무 확인
    check_checkname = fields.Char(string='결재자확인')
    #통보자 유무 확인
    check_reference = fields.Char(string='통보자확인')
    #상신일 
    confirm_date = fields.Date('confirm_date')
    #결재와 반려버튼 제어
    check = fields.Boolean(string='check',compute='_compute_check')
    #권한검사
    check_inspection = fields.Boolean(default = True)
    check_all = fields.Boolean('전결')
    #다음결재자확인
    next_check = fields.Char(string='next_check',compute='_compute_next_check', store=True)
    #현재문서 결재상태
    state = fields.Selection([
        ('temp', '임시저장'),
        ('write', '상신'),
        ('ing', '진행중'),
        ('cancel', '반려'),
        ('remove', '취소'), 
        ('done', '결재완료')],string='Status', readonly=True, index=True, copy=False, default='temp', track_visibility='onchange')
    #연차개수
    holiday_count = fields.Char('holiday_count', compute='_compute_holiday_count')

    my_doc_count = fields.Integer('my_doc', compute='_compute_my_check_count')
    my_check_count = fields.Integer('my_check', compute='_compute_my_check_count')
    my_ref_count = fields.Integer('my_ref', compute='_compute_my_check_count')
    create_date = fields.Date('create_date',default=fields.Datetime.now)

    #달력
    date_from = fields.Date('start',required=True, default=fields.Datetime.now)
    date_to = fields.Date('end', default=fields.Datetime.now)

    #근태신청서_리프레시확인 
    refresh_date_to = fields.Date('start',default=fields.Datetime.now)
    refresh_date_from = fields.Date('end',default=fields.Datetime.now)
    refresh_num = fields.Integer(store=True,compute='_refresh_check')
    refresh_use_num = fields.Integer(store=True,compute='_refresh_check')
    refresh_days = fields.Integer(store=True,compute='_refresh_check')

    #업무요청확인서
    item = fields.Selection([('individual','개인'),('business','업무')],default='individual')
    etc = fields.Text(string='기타',store=True)
    price = fields.Char(string='발생비용',store=True)
    request = fields.Text(string='요청사유',store=True)  

    #view
    project_many = fields.Many2many('project.project',string='프로젝트')
    project = fields.Many2one('project.project',string='프로젝트')
    sign = fields.Many2one('gvm.sign', string='sign',required=True)
    cost = fields.One2many('gvm.signcontent.cost','sign', string='cost')
    cost2 = fields.One2many('gvm.signcontent.cost2','sign', string='cost2')
    work = fields.One2many('gvm.signcontent.work','sign', string='work')
    timesheet = fields.Many2many('account.analytic.line','sign','timesheet',domain="[('user_id','=',uid)]",store=True,compute='_onchange_timesheet')
    reason = fields.Text('reason',store=True)
    rest1 = fields.Selection([('day','연차'),
      #오전반차 오후반차 구분
      ('half','오전반차'),
      ('half_2','오후반차'),
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
    relate_sign1 = fields.Many2one('gvm.signcontent',string='출장완료서')
    relate_sign2 = fields.Many2one('gvm.signcontent',string='출장계획서')
    #결재라인
    sign_line = fields.One2many('gvm.signcontent.line','sign','sign_line')
    #출장신청서
    companion = fields.Char('동행자')
    material1 = fields.Selection([('no','없음'), ('material','자재'), ('tool','공구'), ('etc','기타')], default ='no')
    material2 = fields.Char('출장자재항목')
    request = fields.Char('고객사담당자')
    request_phone = fields.Char('고객사연락처')
    education = fields.Selection([('need','필요'), ('needless','불필요')], default='need')
    education_date = fields.Date('교육날짜',default=fields.Datetime.now)
    visit = fields.Selection([('confirm','승인완료'), ('no','미신청'), ('ing','승인대기')], default='confirm')
    category = fields.Selection([('survey','설계실측'),
        ('setup','셋업'),
        ('gratisAS','무상A/S'),
        ('lactealAS','유상A/S'),
        ('oncall','OnCall'),
        ('breakup','해체'),
        ('etc','기타')], default='survey')
    category_etc = fields.Char('출장 업무')

    @api.depends('date_from','date_to','job_ids')
    def _compute_basic_cost(self):
        for record in self:
         if record.date_to and record.date_from:
           fmt = '%Y-%m-%d'
           d1 = datetime.strptime(record.date_to,fmt)
           d2 = datetime.strptime(record.date_from,fmt)
           dayDiff = str((d1-d2).days+1)
           job_id = record.job_ids.no_of_hired_employee
           record.basic_cost = 0
	   
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

    
    #현재결재자와 로그인한 사람이 일치 하는지 파악
    @api.model
    def _check_me(self):
        for record in self: 
          #현재결재자와 로그인한 사람이 일치 하는지 파악
          if record.next_check == self.env.user.name: return True

    #_check_me 수행후, 실행되는함수
    @api.model
    def _compute_check(self):
        for record in self:
          #True 상태일경우
          if record._check_me():
             #상신, 진행중일때
             if record.state == 'write' or record.state == 'ing':
                 #결재버튼을 보여준다.
                 record.check = True

    @api.depends('state')
    def _compute_next_check(self):
     if self.state != 'temp':
       for record in self:
         #다음 결재자를 찾는다.
         check_id_list = record.get_check_list()
        
    @api.depends('user_id')
    def _compute_holiday_count(self):
      for record in self:
	hr_name = self.env['hr.employee'].sudo(1).search([('name','=',record.user_id.name)])
        record.holiday_count = hr_name.holiday_count

    @api.model
    def _compute_my_check_count(self):
      my_doc = self.env['gvm.signcontent'].search([('user_id','=',self.env.uid)])
      for record in self:
        record.my_doc_count = len(my_doc)
        record.my_check_count = len(my_check_doc)
        record.my_ref_count = len(my_ref_doc)
   
    @api.depends('rest1','refresh_date_to','refresh_date_from')
    def _refresh_check(self):
      for record in self:
        if record.rest1 == 'refresh':
          #출장비정산서찾기     
          sign = self.env['gvm.signcontent'].search([('user_id','=',self.env.uid),('sign','=','출장비정산서')],limit=1)
                    
          #출장비정산을 한번도 작성하지 않은경우
          if sign.date_to == False:
            date_to = record.refresh_date_to
            date_from = record.refresh_date_from
          #본인이 날짜를 수정했을경우  
          elif sign.date_to != record.refresh_date_to: 
            date_to = record.refresh_date_to
            date_from = record.refresh_date_from
          #출장비정산서를 작성한경우
          else:
            record.refresh_date_to = sign.date_from
            record.refresh_date_from = sign.date_to
            date_to = sign.date_from
            date_from = sign.date_to

          #리프레시계산
          datefrom = datetime.strptime(date_from, '%Y-%m-%d')
          dateto = datetime.strptime(date_to, '%Y-%m-%d')
          num = datefrom - dateto 
          num = str(num)
          #출장비정산서(Datetime):days, 출장기간(Date):day
          if sign.date_to == False:
              num = num.split(' days')
          else:
              num = num.split(' day')
          num = num[0]
          if num not in '00:00:00':
             record.refresh_num = int(num) / 30              
             record.refresh_days = int(num)
          else:
             record.refresh_days = 0
             record.refresh_num = 0
            
          #현재 연차개수 계산
          self_dateto = datetime.strptime(record.date_to, '%Y-%m-%d')
          self_datefrom = datetime.strptime(record.date_from, '%Y-%m-%d') 
          self_num = self_datefrom - self_dateto 
          self_num = str(self_num)  
          self_num = self_num.split(' day')
          self_num = self_num[0]
          if self_num not in '00:00:00':
             record.refresh_use_num = int(self_num) + 1
          else: 
             record.refresh_use_num = 1

    #기본 결재자 선택
    @api.onchange('sign_ids')
    def _default_check1(self):
        for record in self:
          user = self.env.uid
          dep = self.env['hr.department'].search([('member_ids.user_id','=',user)],limit=1)
          boss = dep.manager_id
          management = self.env['hr.employee'].search([('department_id','=',10)])
          ceo = self.env['hr.employee'].search([('id','=',126)])
          present_user =  self.env['hr.employee'].search([('user_id','=',user)]) 
	  management_manager = management[0]

          #부서장일경우 대표님으로 결재
          if present_user == boss:
            boss = ceo
          #check: 결재(sign), 합의(2), 통보(3) / state : 0 (대기) / sequnce : 순번 
          if record.sign_ids in [2,3]:
            record.sign_line = [(0, 0, {'name':boss.id, 'check':'sign','state':'0','sequence':'0'}),
                                (0, 0, {'name':management[1].id, 'check':'2','state':'0','sequence':'1'}),
                                (0, 0, {'name':management_manager.id, 'check':'2','state':'0','sequence':'2'}),
                               ]
          elif record.sign_ids in [4,6]:
            if boss.id != ceo.id:
                record.sign_line = [(0, 0, {'name':boss.id, 'check':'sign','state':'0','sequence':'0'}),
                                    (0, 0, {'name':ceo.id, 'check':'sign','state':'0','sequence':'1'}),
                                   ]
            else:
                record.sign_line = [(0, 0, {'name':ceo.id, 'check':'sign','state':'0','sequence':'0'}),
                                   ]
          elif record.sign_ids == 5:
            record.sign_line = [(0, 0, {'name':boss.id, 'check':'sign','state':'0','sequence':'0'}),
                                (0, 0, {'name':management[2].id, 'check':'2','state':'0','sequence':'1'}),
                               ]
	  elif record.sign_ids == 1:
            record.sign_line = [(0, 0, {'name':boss.id, 'check':'sign','state':'0','sequence':'0'}),
                                (0, 0, {'name':management[1].id, 'check':'3','state':'0','sequence':'1'}),
                               ]
          else:
            record.sign_line = [(0, 0, {'name':boss.id, 'check':'sign','state':'0','sequence':'0'}),
                               ]

    @api.depends('date_from','date_to')
    def _onchange_timesheet(self):  
      #리프레시_날짜를변경할경우
      self_dateto = datetime.strptime(self.date_from, '%Y-%m-%d')
      self_datefrom = datetime.strptime(self.date_to, '%Y-%m-%d') 
      self_num = self_datefrom - self_dateto 
      self_num = str(self_num)  
      self_num = self_num.split(' day')
      self_num = self_num[0]

      if self_num not in '00:00:00':
        self.refresh_use_num = int(self_num) + 1
      else: 
         self.refresh_use_num = 1

      for record in self:
        if record.sign_ids == 2:
	 #잔업특근기간수정
         date_from = datetime.strptime(record.date_from, '%Y-%m-%d')
         date_from = date_from + dt.timedelta(hours=-9)
         worktime = self.env['account.analytic.line'].search([('date_from','>=',str(date_from)),('date_to','<=',record.date_to),('user_id','=',record.user_id.id),('unit_amount','>=',1)])
         record.timesheet = worktime

    @api.model
    def _check_high_job_id(self):
        for record in self:
          if record.user_job_id.no_of_hired_employee >= 4 and record.job_ids.no_of_hired_employee < record.user_job_id.no_of_hired_employee:return True

    def button_reorder(self):
        #상신으로 상태변경
        sign = self.env['gvm.signcontent'].search([('id','=',self.id)])
        self.sudo(self.user_id.id).write({'state': 'write'})   
        #결재 초기화
        for value in sign.sign_line:
            value.write({
                 'check_date':None,
                 'state':'0',
                 'check_checkname':'',
                 'check_mail':False
            })
        #결재정보를 다시 얻어 결재순서를 유지한다.
        self.get_check_list()
        self.sendmail()
    
	#근태신청서
        if self.sign.num == 1:
	 #현재 연차 갯수
         count = self.check_holiday_count()
	 #로그인 유저 정보
         hr_name = self.env['hr.employee'].sudo(1).search([('name','=',self.user_id.name)])
	 #총 연차갯수 - 사용한 연차 갯수
         h_count = float(hr_name.holiday_count) - float(count)
	 #적용
         hr_name.holiday_count = float(h_count)
         text = str('근태재상신 %s -> %s' % (h_count+count, h_count))
         self.env['hr.tracking'].create({'name':hr_name.id,'holiday_count':h_count,'etc':text,'sign_id':self.id})
        return {}
    
    #결재된문서
    @api.multi
    def After_sign_view(self):
        uname = self.env['hr.employee'].search([('user_id','=',self.env.uid)]).id
        username = self.env['hr.employee'].search([('user_id','=',self.env.uid)]).name
        domain = [('sign_line','in',username),('sign_line.check_checkname','=',username)]
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

    #결재할문서
    @api.multi
    def sign_view(self):
        uname = self.env['hr.employee'].search([('user_id','=',self.env.uid)]).id
        username = self.env['hr.employee'].search([('user_id','=',self.env.uid)]).name
        domain = [('next_check','=',username),('state','not in',['temp','cancel','remove'])]
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

    #참조문서
    @api.multi
    def sign_reference_view(self):
        uname = self.env['hr.employee'].search([('user_id','=',self.env.uid)]).id
        username = self.env['hr.employee'].search([('user_id','=',self.env.uid)]).name
        domain = [('sign_line','in',username),('sign_line.check_reference','=',username),('state','not in',['temp','cancel','remove'])]
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

    def return_holiday_count(self):
         #근태신청서
	 if self.sign.num == 1:
	  #연차갯수
	  count = self.check_holiday_count()
	  #로그인한 유저정보
	  hr_name = self.env['hr.employee'].sudo(1).search(['&',('name','=',self.user_id.name),('department_id','=',self.dep_ids.id)])
	  #총 연차갯수 + 사용했던 연차갯수
	  h_count = float(hr_name.holiday_count) + float(count)
	  # 적용
	  hr_name.holiday_count = float(h_count)

    #취소버튼
    def button_remove(self):
      #근태신청서
      if self.sign.num == 1:
	 #연차갯수
	 count = self.check_holiday_count()
	 #로그인한 유저정보
	 hr_name = self.env['hr.employee'].sudo(1).search(['&',('name','=',self.user_id.name),('department_id','=',self.dep_ids.id)])
         _logger.warning("name%s"%self.user_id.name)
         _logger.warning("depart%s"%self.dep_ids.id)
	 #총 연차갯수 + 사용했던 연차갯수
	 h_count = float(hr_name.holiday_count) + float(count)
	 # 적용
         hr_name.holiday_count = float(h_count)
         text = str('근태 취소 %s -> %s' % (h_count+count, h_count))
         self.env['hr.tracking'].create({'name':hr_name.id,'holiday_count':h_count,'etc':text,'sign_id':self.id})
	 #상태 정보: 취소상태
         self.write({'state':'remove'})

      #상태 정보: 취소상태
      self.write({'state':'remove'})

    #상신버튼 눌렀을경우 동작함수
    def button_confirm(self):
      for record in self:
       #결재정보를 얻는다.
       check_id_list = record.get_check_list()
         
       #중복검사
       for check in check_id_list:
           if len(check_id_list) > len(filter(lambda x:x[1]!=check[1], check_id_list))+1:
             raise UserError(_('결재라인은 중복되면 안됩니다.'))
           #권한검사Flag     
           if "sign" in check:
             record.check_inspection = False

       #권한검사
       #결재자가 없을경우 상신할 수 없다.
       if record.check_inspection == True:
           raise UserError(_('결재자가 없습니다. 결재라인을 확인하세요.'))
 
      #연차 개수
      if self.sign.num == 1:
         count = self.check_holiday_count()
	 hr_name = self.env['hr.employee'].sudo(1).search([('name','=',self.user_id.name)])
	 h_count = float(hr_name.holiday_count) - float(count) 
         hr_name.holiday_count = float(h_count)

         #if h_count < -7:
         # raise UserError(_('사용 가능한 연차 개수를 초과하셨습니다.'))
       
      self.sendmail()
      #처음 결재자에게 메일을 보낸다.
      self.write({'state':'write',
                  'confirm_date':datetime.today()
      })

    def check_holiday_count(self, rest1=None, date_to=None, date_from=None):
        count = 0
        #포상연차인지 아닌지 구분
	if rest1 != None:
	   rest = rest1
	   date_to = date_to
	   date_from = date_from
	else:
	   rest = self.rest1
	   date_to = self.date_to
	   date_from = self.date_from
        
        #포상연차일경우    
	if rest in ['refresh','publicvacation','special']:
	  return count
    
	#오전반차 오후반차 구분  
	if rest == 'half':
	  count = 0.5
	  return count
	elif rest == 'half_2':
	  count = 0.5
	  return count
	elif rest == 'quarter':
	  count = 0.25
	  return count
	
        #연차일경우 갯수 파악  
        fmt = '%Y-%m-%d'
        d1 = datetime.strptime(date_to,fmt)
        d2 = datetime.strptime(date_from,fmt)
        days = (d1-d2).days + 1

        """ weekday : 0->월, 1->화, 2->수, 3-> 목, 4->금, 5->토 6->금 """
        #시작일 요일 파악
        week_start = d2.weekday()
        week_end = d1.weekday()
        
        """ 주단위로 계산하여, 주말을 구함 """
        #일주일이 넘었을경우
        if days > 6:
          #주 계산
          week = days / 7
          #예외)만약 시작일이 일요일인 경우, 마지막일이 토요일인 경우
          if week_start == 6 or week_end == 5:
            days = days - 1
          #주말계산
          count = days - (week * 2)
        else:
          #시작일을 저장
          date_from = d2
          #기간(마지막일 - 시작일)만큼 for문을 돌린다.
          for i in range(days):
            #증가된 날짜를 가져오기 위해 한번더 저장
            date_from = date_from 
            #각각의 날짜 별로 요일을 구한다.
            weekday = date_from.weekday()
            #주말이 아닐경우
            if weekday != 5 and weekday != 6:
                count = count + 1
            #요일을 구하기위해 날짜를 증가시킨다.
            date_from = date_from + dt.timedelta(days=1)

	return count

    def gvm_sign_comment(ids, comment, state=None):
      _logger.warning('comment start')
      #현재페이지의 결재문서 번호를 가져온다.
      Model = request.env['gvm.signcontent']
      sign_id = Model.search([('id','=',ids.id)],limit=1)
      name = request.env.user.name
      receiver = []

#_______________결재라인관리
      #결재버튼 클릭시
      if not state:
        _logger.warning('click permit')
        #결재(결재자가 결재시 통보자도 같이 결재된다)
        for record in sign_id.sign_line:
          if record.check_mail == True and record.check_date == False:
            #결재자
            if record.check == 'sign' or record.check == '2':
               record.sudo(1).write({
                    'check_date':datetime.now(),
                    'check_checkname':name,
                    'state':'1',
                    'reason':comment
               })
            #통보자
            else:
               record.sudo(1).write({
                    'check_date':datetime.now(),
                    'check_checkname':name,
                    'state':'1',
               })
          if record.check_date == False:
            #진행상태: 진행중
            if record.state == '0':
              state = 'ing'
            #sign_line 결재 상태일떄
          if record.state == '1':
              state = 'done'
      #반려버튼 클릭시
      else:
        _logger.warning('click deny')
        if state == 'cancel':
          #결재버튼을 숨긴다.
          sign_id.check = False
          #현재 서버 페이지의 정보를 가져온다.
	  rest1 = sign_id.rest1
          date_to = sign_id.date_to
          date_from = sign_id.date_from
          #연차의 갯수를 상신 전상태로 돌린다.
          count = sign_id.check_holiday_count(rest1,date_to,date_from)
          hr_name = request.env['hr.employee'].search([('name','=',sign_id.user_id.name)])
          h_count = float(hr_name.holiday_count) +  float(count)
          hr_name.write({
                  'holiday_count': h_count
          })
          text = str('근태 반려 %s -> %s' % (h_count+count, h_count))
          request.env['hr.tracking'].create({'name':hr_name.id,'holiday_count':h_count,'etc':text,'sign_id':sign_id.id})
          #다음 결제권한을  작성자에게 넘긴다. 
          sign_id.next_check = sign_id.writer

          for record in sign_id.sign_line:
            #결재시간이없고 자기자신일경우
            if record.check_date == False:
              if record.name.name == name:
                    record.write({
                        'state':'4',
                        'reason':comment,
                        'check_checkname':name,
                        'check_date':datetime.now()
                    })
      sign_id.sudo(1).write({'state':state})

#_____________________메일보내기
      check = False
      post = '결재문서'
      Flag = 0
      for record in sign_id.sign_line:
        #결재라인: 다음 결재자에게 메일보내기
        if record.check_date == False:
          if (record.check == 'sign' or record.check == '2') and check != True:
             receiver.append(record.name)
             _logger.warning("record%s"%record)
             record.write({'check_mail':True})
             check = True
          elif record.check == '3':
             receiver.append(record.name)
             _logger.warning("record%s"%record)
             record.write({'check_mail':True})
          else:
             break
          #반려시 메일보내기
          if record.check != '3' and state == 'cancel':
            post = '님에 의하여 반려되었습니다. 결재문서를 확인하세요.'
            receiver.append(record.name)
            Flag = 1

      _logger.warning('send mail')
      sender = request.env.user.name
      #메타데이터 id
      post_id = sign_id.id
      #문서번호(S0001)
      po_num = str(sign_id.name)
      #사용모델위치
      model_name = 'gvm.signcontent'
      #링크에서 찾아서 쓰면됨
      #현재페이지 위치 찾는 용도(리스트)
      menu_id = "316"
      action_id = "423"
      send_mail = gvm_mail().gvm_send_mail(sender, receiver, post, post_id, po_num, model_name, menu_id, action_id,Flag)
      _logger.warning('comment finish')
    
    @api.model
    def create(self, vals):
        if vals.get('name','New') == 'New':
           vals['name'] = self.env['ir.sequence'].next_by_code('gvm.sign.number') or '/'
        res = super(GvmSignContent, self).create(vals)
        res.check_confirm = True
	return res

    #삭제되었을경우
    @api.multi
    def unlink(self):        
        for record in self:
            if not record.user_id.name == self.env.user.name:
                raise UserError(_('본인 외 삭제 불가'))
	    elif record.state != 'temp':
	      #삭제되었을경우 연차 갯수 복귀
	      #근태신청서. 상신 시 개수 조정 되므로 상신 안되었을 때, 반려일 때 안깎음
	      if record.sign.num == 1 and record.state not in ['temp','cancel']:
	        #연차갯수
	        count = self.check_holiday_count()
	        #로그인한 유저정보
	        hr_name = self.env['hr.employee'].sudo(1).search(['&',('name','=',record.user_id.name),('department_id','=',record.user_department.id)])
	        #총 연차갯수 + 사용했던 연차갯수
	        h_count = float(hr_name.holiday_count) + float(count)
	        # 적용
	        hr_name.holiday_count = float(h_count)
                text = str('근태 삭제 %s -> %s' % (h_count+count, h_count))
                self.env['hr.tracking'].create({'name':hr_name.id,'holiday_count':h_count,'etc':text,'sign_id':self.id})
        return super(GvmSignContent, self).unlink()

    @api.multi
    def write(self, vals):
        #[취소권한부여] 294: 유예진, 295: 이승현, 258: 김진우, 316: 조나래
        allower = [1,294,295,258,316]
        for record in self:
            if record.state in ['temp','write','cancel','remove']:
	     if self.env.user.name != record.user_id.name and self.env.uid != 1:
               raise UserError(_('본인 외 수정 불가'))
            else:
             if self.sign_ids != 10:
                 if self.env.uid not in allower:
                    raise UserError(_('이미 결재가 진행 중인 문서는 수정이 불가합니다.'))
        return super(GvmSignContent, self).write(vals)

    #결재 정보를 가져온다.(통보자제외)
    def get_check_list(self):
        #결재 정보
    	check_list = self.sign_line
        check_id_list = []

        for record in self:
          for value in check_list:
            #결재권한이 없는 통보는 제외
            if value.check != '3':
              #결재 완료자 제외
              if value.check_date == False:
                #결재 정보 추가
                check_id_list.append([value.check,value.name.name])
            #통보일경우
            elif value.check == '3':
                value.write({'check_reference':value.name.name})
        
          #for문을 두번 돌린이유: 위-> 정보추가/ 아래-> 조건문생성
          for value in check_id_list:
            #첫번쩨 결재자
            record.next_check = check_id_list[0][1]
          if not check_id_list:    
            #다음 결재자가 없을경우
            record.next_check = ''
          #결재가 완료되었을경우
          if record.next_check == '':
            #결재버튼을 숨긴다.
            record.check = False
        return check_id_list
    
    #처음 결재자,통보자에게만 메일을 보낸다.
    #결재가 진행된 후에는 controllers 에서 관리
    def sendmail(self):
        check_id_list = self.sign_line
        count = len(check_id_list)
        receiver=[]

        if count < 2:
          if check_id_list.check != '3':
            receiver.append(check_id_list.name)
            check_id_list.write({'check_mail':True})
        
        #결재자와 통보자를 찾을때까지 돌려야함
        else: 
            check = False
            for value in check_id_list:
             if check == False:
               if value.check != '3':
                  receiver.append(value.name)
                  value.write({'check_mail':True})
             else:
               if value.check == 'sign' or value.check == '2':
                  break
               else:
                 receiver.append(value.name)
                 value.write({'check_mail':True})
             check = True
              
        gvm = gvm_mail()
        #메타데이터 id
        post_id = self.id
        #문서번호(S0001)
        po_num = str(self.name)
        #사용모델위치
        model_name = 'gvm.signcontent'
        #링크에서 찾아서 쓰면됨
        #현재페이지 위치 찾는 용도(리스트)
        menu_id = "316"
        action_id = "423"
        gvm.gvm_send_mail(self.env.user.name, receiver, '결재문서', post_id, po_num, model_name, menu_id, action_id)

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

    @api.onchange('cost')
    def get_currency(self):
      if self.cost > 100000:
        self.currency = 'dong'
      elif self.cost > 1000:
        self.currency = 'won'
      elif self.cost <= 1000:
        self.currency = 'yuan'

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
    _order = 'sequence'

    @api.model
    def default_sequence(self):
        return  self.env['ir.sequence'].next_by_code('gvm.signline.number')
    
    name = fields.Many2one ('hr.employee' ,string = 'name', required=True)
    sequence = fields.Integer (' 순번 ', default=default_sequence)
    check_mail = fields.Boolean(default=False) 
    check = fields.Selection ([( 'sign' , '결재' ), ( '2' , '합의' ), ( '3' , '통보' )], default='sign')
    state = fields.Selection ([('0', '대기' ),( '1' , '결재' ), ( '2' , '합의' ), ( '3' , '통보' ), ( '4' , '반려' )], default='0', readonly=True)
    sign = fields.Many2one ('gvm.signcontent' , 'sign')
    check_date = fields.Datetime('check_date', readonly=True)
    next_check = fields.Char(string='결재예정', compute='_compute_next_check',store=True)
    reason = fields.Text('reason', readonly=True)
    check_reference = fields.Char(string='통보자확인')
    check_checkname = fields.Char(string='결재자확인')
