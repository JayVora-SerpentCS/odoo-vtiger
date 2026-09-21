# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    vtiger_id = fields.Char("VTiger ID", readonly=True, copy=False, index=True)
    vtiger_source_module = fields.Char(
        "VTiger Source Module", readonly=True, copy=False
    )
    vtiger_ticket_no = fields.Char("VTiger Ticket No", readonly=True, copy=False)
    vtiger_status = fields.Char("VTiger Status", readonly=True)
    vtiger_category = fields.Char("VTiger Category", readonly=True)
    vtiger_severity = fields.Char("VTiger Severity", readonly=True)
    vtiger_solution = fields.Text("VTiger Solution", readonly=True)
    vtiger_createdtime = fields.Datetime("VTiger Created Time", readonly=True)
    vtiger_modifiedtime = fields.Datetime("VTiger Modified Time", readonly=True)
