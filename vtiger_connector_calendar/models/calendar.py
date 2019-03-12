# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
from odoo import fields, models


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    vtiger_id = fields.Char('VTiger ID', readonly=True)
