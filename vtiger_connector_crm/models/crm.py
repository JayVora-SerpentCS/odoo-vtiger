# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    vtiger_id = fields.Char('VTiger ID', readonly=True, copy=False)
