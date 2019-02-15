# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, SUPERUSER_ID, _

class ProjectChecklist1(models.Model):
    """ Tags of project's tasks (or issues) """
    _name = "project.checklist1"
    _description = "Tags of project's tasks, issues..."

    name = fields.Char(required=True)
    color = fields.Integer(string='Color Index', default=1)
    department = fields.Char('부서')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists !"),
    ]
class ProjectChecklist2(models.Model):
    """ Tags of project's tasks (or issues) """
    _name = "project.checklist2"
    _description = "Tags of project's tasks, issues..."

    name = fields.Char(required=True)
    color = fields.Integer(string='Color Index', default=2)
    department = fields.Char('부서')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists !"),
    ]
class ProjectChecklist3(models.Model):
    """ Tags of project's tasks (or issues) """
    _name = "project.checklist3"
    _description = "Tags of project's tasks, issues..."

    name = fields.Char(required=True)
    color = fields.Integer(string='Color Index', default=3)
    department = fields.Char('부서')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists !"),
    ]
class ProjectChecklist4(models.Model):
    """ Tags of project's tasks (or issues) """
    _name = "project.checklist4"
    _description = "Tags of project's tasks, issues..."

    name = fields.Char(required=True)
    color = fields.Integer(string='Color Index', default=4)
    department = fields.Char('부서')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists !"),
    ]
class ProjectChecklist5(models.Model):
    """ Tags of project's tasks (or issues) """
    _name = "project.checklist5"
    _description = "Tags of project's tasks, issues..."

    name = fields.Char(required=True)
    color = fields.Integer(string='Color Index')
    department = fields.Char('부서')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists !"),
    ]
