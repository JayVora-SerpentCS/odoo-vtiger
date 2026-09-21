# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class DocumentsDocument(models.Model):
    _inherit = "documents.document"

    vtiger_id = fields.Char("VTiger ID", readonly=True, copy=False, index=True)
    vtiger_document_no = fields.Char("VTiger Document No", readonly=True, copy=False)
    vtiger_filename = fields.Char("VTiger Filename", readonly=True)
    vtiger_filesize = fields.Integer("VTiger File Size", readonly=True)
    vtiger_filetype = fields.Char("VTiger File Type", readonly=True)
    vtiger_folder_id = fields.Char("VTiger Folder ID", readonly=True)
    vtiger_document_source = fields.Char("VTiger Document Source", readonly=True)
    vtiger_document_type = fields.Char("VTiger Document Type", readonly=True)
    vtiger_notecontent = fields.Text("VTiger Notes", readonly=True)
    vtiger_createdtime = fields.Datetime("VTiger Created Time", readonly=True)
    vtiger_modifiedtime = fields.Datetime("VTiger Modified Time", readonly=True)
