# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    vtiger_id = fields.Char('VTiger ID', readonly=True)
