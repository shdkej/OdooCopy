# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from datetime import datetime,timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools.translate import _
import logging
from urllib2 import Request, urlopen
from urllib import urlencode, quote_plus

_logger = logging.getLogger(__name__)


class AccountAnalyticTag(models.Model):
    _name = 'account.analytic.tag'
    _description = 'Analytic Tags'
    name = fields.Char(string='Analytic Tag', index=True, required=True)
    color = fields.Integer('Color Index')


class AccountAnalyticAccount(models.Model):
    _name = 'account.analytic.account'
    _inherit = ['mail.thread']
    _description = 'Analytic Account'
    _order = 'code, name asc'

    @api.multi
    def _compute_debit_credit_balance(self):
        analytic_line_obj = self.env['account.analytic.line']
        domain = [('account_id', 'in', self.mapped('id'))]
        if self._context.get('from_date', False):
            domain.append(('date', '>=', self._context['from_date']))
        if self._context.get('to_date', False):
            domain.append(('date', '<=', self._context['to_date']))

        account_amounts = analytic_line_obj.search_read(domain, ['account_id', 'amount'])
        account_ids = set([line['account_id'][0] for line in account_amounts])
        data_debit = {account_id: 0.0 for account_id in account_ids}
        data_credit = {account_id: 0.0 for account_id in account_ids}
        for account_amount in account_amounts:
            if account_amount['amount'] < 0.0:
                data_debit[account_amount['account_id'][0]] += account_amount['amount']
            else:
                data_credit[account_amount['account_id'][0]] += account_amount['amount']

        for account in self:
            account.debit = abs(data_debit.get(account.id, 0.0))
            account.credit = data_credit.get(account.id, 0.0)
            account.balance = account.credit - account.debit

    name = fields.Char(string='Analytic Account', index=True, required=True, track_visibility='onchange')
    code = fields.Char(string='Reference', index=True, track_visibility='onchange')
    active = fields.Boolean('Active', help="If the active field is set to False, it will allow you to hide the account without removing it.", default=True)

    tag_ids = fields.Many2many('account.analytic.tag', 'account_analytic_account_tag_rel', 'account_id', 'tag_id', string='Tags', copy=True)
    line_ids = fields.One2many('account.analytic.line', 'account_id', string="Analytic Lines")

    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)

    # use auto_join to speed up name_search call
    partner_id = fields.Many2one('res.partner', string='Customer', auto_join=True, track_visibility='onchange')

    balance = fields.Monetary(compute='_compute_debit_credit_balance', string='Balance')
    debit = fields.Monetary(compute='_compute_debit_credit_balance', string='Debit')
    credit = fields.Monetary(compute='_compute_debit_credit_balance', string='Credit')

    currency_id = fields.Many2one(related="company_id.currency_id", string="Currency", readonly=True)

    @api.multi
    def name_get(self):
        res = []
        for analytic in self:
            name = analytic.name
            if analytic.code:
                name = '['+analytic.code+'] '+name
            if analytic.partner_id:
                name = name +' - '+analytic.partner_id.commercial_partner_id.name
            res.append((analytic.id, name))
        return res

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if operator not in ('ilike', 'like', '=', '=like', '=ilike'):
            return super(AccountAnalyticAccount, self).name_search(name, args, operator, limit)
        args = args or []
        domain = ['|', ('code', operator, name), ('name', operator, name)]
        partners = self.env['res.partner'].search([('name', operator, name)], limit=limit)
        if partners:
            domain = ['|'] + domain + [('partner_id', 'in', partners.ids)]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()


class AccountAnalyticLine(models.Model):
    _name = 'account.analytic.line'
    _description = 'Analytic Line'
    _order = 'date desc, id desc'

    @api.model
    def _default_user(self):
        return self.env.context.get('user_id', self.env.user.id)

    name = fields.Text('요약', required=True)
    date = fields.Date('Date', default=fields.Date.context_today)
    amount = fields.Monetary('Amount', required=True, default=0.0)
    unit_amount = fields.Float('Quantity', default=0.0,compute='_compute_basic_cost', store=True)
    account_id = fields.Many2one('account.analytic.account', 'Analytic Account', ondelete='restrict')
    partner_id = fields.Many2one('res.partner', string='Partner')
    user_id = fields.Many2one('res.users', string='User', default=_default_user)

    tag_ids = fields.Many2many('account.analytic.tag', 'account_analytic_line_tag_rel', 'line_id', 'tag_id', string='Tags', copy=True)

    company_id = fields.Many2one(related='account_id.company_id', string='Company', store=True, readonly=True)
    currency_id = fields.Many2one(related="company_id.currency_id", string="Currency", readonly=True)
    detail = fields.Text('상세내용')
    date_from = fields.Datetime(string='시작 시간',default=lambda *a:datetime.now().replace(hour=0,minute=00).strftime("%Y-%m-%d %H:%M:%s"))
    date_to = fields.Datetime('종료 시간',default=fields.Datetime.now)
    test_date_from = fields.Datetime('test',compute='_compute_mobile_date')
    mobile_date_from = fields.Char('시작시간',store=True)
    mobile_date_to = fields.Char('종료 시간')
    sign = fields.Many2one('gvm.signcontent','sign')
    weekend = fields.Boolean('weekend',compute='_compute_basic_cost')
    lunch = fields.Selection([('0','0'),('1','1'),('2','2'),('3','3')],string='식사횟수', default='2')
    holiday = fields.Boolean('공휴일')

    @api.depends('date_from','date_to','lunch','holiday')
    def _compute_basic_cost(self):
        for record in self:
         if record.date_to and record.date_from:
           fmt = '%Y-%m-%d %H:%M:%S'
           td = timedelta(hours=9)
           d1 = datetime.strptime(record.date_to,fmt) + td
           d2 = datetime.strptime(record.date_from,fmt) + td
           day_end_standard = d2.replace(hour=18, minute=00)
           dayDiff = d1-day_end_standard
	   weekendDiff = d1-d2
           count = (dayDiff.total_seconds()+60) / 3600
	   if d2.weekday() > 4 or record.holiday:
	     record.weekend = True
	     count = (weekendDiff.total_seconds()+60) / 3600
	   if d2.hour >= 18:
	     count = (weekendDiff.total_seconds()+60) / 3600

	   if record.lunch != '0':
	     count = count - int(record.lunch) + 1
           if count <= 0:
             count = 0
	   if count:
	     dot = (count - int(count)) * 10
	     if dot >= 5:
	       count = int(count) + 0.5
	     else:  
	       count = int(count)
	     if d2.weekday() > 4 or record.holiday:
	       count = count * 1.2
             record.unit_amount = count
           #record.sudo(1).write({'date':d2.date()})

    @api.onchange('date_from','date_to')
    def _onchage_lunch(self):
         if self.date_to and self.date_from:
           fmt = '%Y-%m-%d %H:%M:%S'
           td = timedelta(hours=9)
           d1 = datetime.strptime(self.date_to,fmt) + td
           d2 = datetime.strptime(self.date_from,fmt) + td
	   lunch_count = 0
	   if d2.hour < 13 and d1.hour > 12 or d1.hour < 9:
	     lunch_count += 1
	   if d2.hour < 19 and d1.hour > 18 or d1.hour < 9:
	     lunch_count += 1
	   lunch_count = str(lunch_count)
	   _logger.warning(lunch_count)
	   self.lunch = lunch_count

    @api.onchange('date_from')
    def _compute_holiday(self):
         fmt = '%Y-%m-%d %H:%M:%S'
         td = timedelta(hours=9)
         for record in self:
           d2 = datetime.strptime(record.date_from,fmt) + td
	   date = str(d2.date()).replace('-','')
	   isHoliday = self.isHoliday(date)
	   record.holiday = False
	   if isHoliday:
	     record.holiday = True

    def isHoliday(self, date):
	state = False
	solYear = str(datetime.today().year)
	filename = '/usr/lib/python2.7/dist-packages/odoo/addons/gvm/test_'+solYear+'.xml'
	f = open(filename)
	info = f.read()
	holiday = []

	split_s = info.split('<locdate>')
	for s in split_s:
	  holiday.append(s[0:8])

	if date in holiday:
	  state = True
	  print state

	return state

    def parse_holiday(self):
        url = 'http://apis.data.go.kr/B090041/openapi/service/SpcdeInfoService/getRestDeInfo'
	apiKey = 'j2DHSm20GZ4MePk9FTTUwxHfq7DcShJcARMRP6pvlWbw1pxUBkQPCxp8LAFmgl4uGJq%2Fk%2F8ueK8zt2GOv9QS8g%3D%3D'
	str_tmp = ''
	solYear = str(datetime.today().year)

	for i in range(1,13):
	  if i < 10:
	    i = '0' + str(i)
	  solMonth = str(i)
	  query = '?'+'ServiceKey='+apiKey+'&solYear='+solYear+'&solMonth='+solMonth

	  request = Request(url + query)
	  request.get_method = lambda: 'GET'
	  response = urlopen(request).read()
	  str_tmp += response

	filename = '/usr/lib/python2.7/dist-packages/odoo/addons/gvm/test_'+solYear+'.xml'
	with open(filename, 'w') as f:
	  f.write(str_tmp)

    @api.depends('mobile_date_from','mobile_date_to')
    def _compute_mobile_date(self):
      fmt = '%Y-%m-%d %H:%M'
      m_date_from = ''
      m_date_to = ''
      td = timedelta(hours=9)
      if self.mobile_date_from:
       date_from = self.mobile_date_from.replace('T',' ')
       m_date_from = datetime.strptime(date_from,fmt) - td
      if self.mobile_date_to: 
       date_to = self.mobile_date_to.replace('T',' ')
       m_date_to = datetime.strptime(date_to,fmt) - td
      if m_date_from:
        self.test_date_from = m_date_from
        self.date_from = m_date_from
      if m_date_to:
        self.date_to = m_date_to

    @api.onchange('date_from')
    def _onchange_date_from(self):
      if self.date_from:
        fmt = '%Y-%m-%d %H:%M:%S'
        td = timedelta(hours=9)
        d1 = datetime.strptime(self.date_from,fmt) + td
        d2 = datetime.strptime(self.date_to,fmt) + td
	if d1.day != d2.day:
          same_day = (datetime.strptime(self.date_from,fmt)+td).replace(hour=10, minute=00)
          self.date_to = same_day
