# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Sign',
    'version': '1.1',
    'category': 'Human Resources',
    'sequence': 80,
    'summary': 'Timesheets, Activities',
    'description': """
Record and validate timesheets and attendances easily
=====================================================

This application supplies a new screen enabling you to manage your work encoding (timesheet) by period. Timesheet entries are made by employees each day. At the end of the defined period, employees validate their sheet and the manager must then approve his team's entries. Periods are defined in the company forms and you can set them to run monthly or weekly.

The complete timesheet validation process is:
---------------------------------------------
* Draft sheet
* Confirmation at the end of the period by the employee
* Validation by the project manager

The validation can be configured in the company:
------------------------------------------------
* Period size (Day, Week, Month)
* Maximal difference between timesheet and attendances
    """,
    'website': 'https://www.odoo.com/page/employees',
    'depends': ['project','purchase'],
    'data': [
        'views/gvm_sign_views.xml',
        'views/gvm_sign_templates.xml',
        'views/project_views.xml',
        'data/gvm_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'qweb': ['static/src/xml/gvm_sign.xml'],
}
