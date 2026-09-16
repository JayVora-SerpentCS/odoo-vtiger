# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ProjectProject(models.Model):
    _inherit = "project.project"

    vtiger_id = fields.Char("VTiger ID", readonly=True, copy=False)


class ProjectTask(models.Model):
    _inherit = "project.task"

    vtiger_id = fields.Char("VTiger ID", readonly=True, copy=False)
