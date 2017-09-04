# -*- coding: utf-8 -*-
from odoo import fields, models


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    vtiger_id = fields.Char('VTiger ID', readonly=True)
