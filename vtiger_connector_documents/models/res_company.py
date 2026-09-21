# See LICENSE file for full copyright and licensing details.

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from odoo import _, fields, models
from odoo.exceptions import UserError


class ResCompany(models.Model):
    _inherit = "res.company"

    last_vtiger_document_sync_date = fields.Datetime(
        string="Last VTiger Document Synced Time"
    )

    def action_sync_vtiger(self):
        self.sync_vtiger_document()
        return super(ResCompany, self).action_sync_vtiger()

    def _execute_vtiger_document_query(self, company, qry, session_name):
        values = {"operation": "query", "query": qry, "sessionName": session_name}
        data = urlencode(values)
        url = company.get_vtiger_server_url()
        req = Request("%s?%s" % (url, data))
        response = urlopen(req, timeout=20)
        return json.loads(response.read())

    def _execute_vtiger_document_retrieve(self, company, vtiger_id, session_name):
        values = {
            "operation": "retrieve",
            "id": vtiger_id,
            "sessionName": session_name,
        }
        data = urlencode(values)
        url = company.get_vtiger_server_url()
        req = Request("%s?%s" % (url, data))
        response = urlopen(req, timeout=20)
        return json.loads(response.read())

    def _build_vtiger_document_query(self, company):
        document_obj = self.env["documents.document"].sudo()
        synced_document = document_obj.search(
            [("vtiger_id", "!=", False), ("company_id", "=", company.id)],
            limit=1,
        )
        documents_without_folder = document_obj.search(
            [
                ("vtiger_id", "!=", False),
                ("vtiger_folder_id", "!=", False),
                ("folder_id", "=", False),
                ("company_id", "=", company.id),
            ],
            limit=1,
        )
        if (
            company.last_vtiger_document_sync_date
            and synced_document
            and not documents_without_folder
        ):
            return "SELECT * FROM Documents WHERE modifiedtime >= '%s';" % (
                company.last_vtiger_document_sync_date
            )
        return "SELECT * FROM Documents;"

    def _to_vtiger_datetime(self, value):
        return fields.Datetime.to_datetime(value) if value else False

    def _vtiger_int(self, value):
        try:
            return int(float(value or 0))
        except (TypeError, ValueError):
            return 0

    def _prepare_vtiger_document_values(self, res, session_name, folder_cache):
        name = res.get("notes_title") or res.get("filename") or res.get("id")
        url = res.get("url") or self._get_vtiger_document_url(res.get("id"))
        folder = self._get_or_create_vtiger_document_folder(
            res.get("folderid"), session_name, folder_cache
        )
        return {
            "name": name,
            "type": "url",
            "url": self._normalize_vtiger_document_url(url),
            "owner_id": self.env.user.id,
            "company_id": self.id,
            "folder_id": folder.id if folder else False,
            "access_internal": "view",
            "vtiger_document_no": res.get("note_no"),
            "vtiger_filename": res.get("filename"),
            "vtiger_filesize": self._vtiger_int(res.get("filesize")),
            "vtiger_filetype": res.get("filetype"),
            "vtiger_folder_id": res.get("folderid"),
            "vtiger_document_source": res.get("document_source"),
            "vtiger_document_type": res.get("document_type"),
            "vtiger_notecontent": res.get("notecontent"),
            "vtiger_createdtime": self._to_vtiger_datetime(res.get("createdtime")),
            "vtiger_modifiedtime": self._to_vtiger_datetime(res.get("modifiedtime")),
        }

    def _normalize_vtiger_document_url(self, url):
        if not url:
            return False
        url = url.strip()
        if url.startswith(("http://", "https://", "ftp://")):
            return url
        if url.startswith("//"):
            return "https:%s" % url
        if url.startswith("/"):
            server = (self.vtiger_server or "").strip().rstrip("/")
            return "%s%s" % (server, url) if server else url
        server = (self.vtiger_server or "").strip().rstrip("/")
        if server:
            if not server.startswith(("http://", "https://", "ftp://")):
                server = "https://%s" % server
            return "%s/%s" % (server, url.lstrip("/"))
        return url

    def _get_vtiger_document_url(self, vtiger_id):
        if not self.vtiger_server or not vtiger_id:
            return False
        server = self.vtiger_server.strip().rstrip("/")
        if not server.startswith(("http://", "https://", "ftp://")):
            server = "https://%s" % server
        record_id = str(vtiger_id).split("x")[-1]
        return "%s/index.php?module=Documents&view=Detail&record=%s" % (
            server,
            record_id,
        )

    def _get_or_create_vtiger_document_folder(
        self, vtiger_folder_id, session_name, folder_cache
    ):
        if not vtiger_folder_id:
            return self.env["documents.document"]
        if vtiger_folder_id in folder_cache:
            return folder_cache[vtiger_folder_id]
        folder_obj = self.env["documents.document"].sudo().with_company(self)
        folder = folder_obj.search(
            [
                ("type", "=", "folder"),
                ("vtiger_id", "=", vtiger_folder_id),
                ("company_id", "=", self.id),
            ],
            limit=1,
        )
        folder_name = self._get_vtiger_document_folder_name(
            vtiger_folder_id, session_name
        )
        if folder:
            if folder_name and folder.name != folder_name:
                folder.write({"name": folder_name})
            folder_cache[vtiger_folder_id] = folder
            return folder
        folder = folder_obj.create(
            {
                "name": folder_name or vtiger_folder_id,
                "type": "folder",
                "owner_id": self.env.user.id,
                "company_id": self.id,
                "access_internal": "view",
                "vtiger_id": vtiger_folder_id,
                "vtiger_document_type": "folder",
            }
        )
        folder_cache[vtiger_folder_id] = folder
        return folder

    def _get_vtiger_document_folder_name(self, vtiger_folder_id, session_name):
        if "x" not in str(vtiger_folder_id):
            return vtiger_folder_id
        result = self._execute_vtiger_document_retrieve(
            self, vtiger_folder_id, session_name
        )
        if result.get("success") and result.get("result"):
            folder = result["result"]
            return (
                folder.get("foldername")
                or folder.get("folder_name")
                or folder.get("name")
                or folder.get("document_folder_name")
                or vtiger_folder_id
            )
        qry = "SELECT * FROM DocumentFolders WHERE id = '%s';" % vtiger_folder_id
        result = self._execute_vtiger_document_query(self, qry, session_name)
        if result.get("success") and result.get("result"):
            folder = result["result"][0]
            return (
                folder.get("foldername")
                or folder.get("folder_name")
                or folder.get("name")
                or folder.get("document_folder_name")
                or vtiger_folder_id
            )
        return vtiger_folder_id

    def _upsert_vtiger_document(self, vals, vtiger_id):
        if not vtiger_id:
            return
        document_obj = self.env["documents.document"].sudo().with_company(self)
        document = document_obj.search([("vtiger_id", "=", vtiger_id)], limit=1)
        if document:
            document.write(vals)
        else:
            vals["vtiger_id"] = vtiger_id
            document_obj.create(vals)

    def _repair_vtiger_document_folders(self, session_name):
        document_obj = self.env["documents.document"].sudo().with_company(self)
        documents = document_obj.search(
            [
                ("vtiger_id", "!=", False),
                ("vtiger_folder_id", "!=", False),
                ("folder_id", "=", False),
                ("company_id", "=", self.id),
                ("type", "!=", "folder"),
            ]
        )
        folder_cache = {}
        for document in documents:
            folder = self._get_or_create_vtiger_document_folder(
                document.vtiger_folder_id, session_name, folder_cache
            )
            if folder:
                document.write({"folder_id": folder.id})

    def sync_vtiger_document(self):
        for company in self:
            access_key = company.get_vtiger_access_key()
            session_name = company.vtiger_login(access_key)
            qry = company._build_vtiger_document_query(company)
            result = company._execute_vtiger_document_query(company, qry, session_name)
            if not result.get("success"):
                raise UserError(
                    _("VTiger Documents sync failed: %s")
                    % (result.get("error") or result)
                )
            folder_cache = {}
            for res in result.get("result", []):
                company._upsert_vtiger_document(
                    company._prepare_vtiger_document_values(
                        res, session_name, folder_cache
                    ),
                    res.get("id"),
                )
            company._repair_vtiger_document_folders(session_name)
            company.last_vtiger_document_sync_date = fields.Datetime.now()
        return True
