# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    vtiger_id = fields.Char('VTiger ID', readonly=True)
