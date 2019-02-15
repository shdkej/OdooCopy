# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Gvm Project Management',
    'version': '1.2',
    'category': 'Projcet',
    'sequence': 60,
    'summary': 'GVM Project Management',
    'description': """
    """,
    'depends': ['project','crm','gvm','purchase'],
    'data': [
        'views/gvm_crm_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
