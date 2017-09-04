# -*- coding: utf-8 -*-
from odoo import api, fields, models


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    vtiger_id = fields.Char('VTiger ID', readonly=True)
