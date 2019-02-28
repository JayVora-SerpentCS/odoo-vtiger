# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    vtiger_id = fields.Char('VTiger ID', readonly=True)
