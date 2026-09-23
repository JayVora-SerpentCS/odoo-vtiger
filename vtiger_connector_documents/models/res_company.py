# See LICENSE file for full copyright and licensing details.

import base64
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import requests

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
        # VTiger documents can keep an old modified date when an uploaded file is
        # moved between folders, so full upsert is safer than incremental sync.
        return "SELECT * FROM Documents;"

    def _to_vtiger_datetime(self, value):
        return fields.Datetime.to_datetime(value) if value else False

    def _vtiger_int(self, value):
        try:
            return int(float(value or 0))
        except (TypeError, ValueError):
            return 0

    def _get_vtiger_rest_api_url(self, endpoint):
        server = (self.vtiger_server or "").strip().rstrip("/")
        if not server:
            return False
        if not server.startswith(("http://", "https://")):
            server = "https://%s" % server
        return "%s/restapi/v1/vtiger/default/%s" % (server, endpoint)

    def _get_vtiger_document_attachment_id(self, res):
        attachment_ids = (
            res.get("imageattachmentids")
            or res.get("fileattachmentid")
            or res.get("attachmentid")
        )
        if not attachment_ids:
            return False
        return str(attachment_ids).split(",")[0].strip()

    def _fetch_vtiger_document_file(self, res):
        attachment_id = self._get_vtiger_document_attachment_id(res)
        url = self._get_vtiger_rest_api_url("files_retrieve")
        if not attachment_id or not url or not self.user_name or not self.access_key:
            return {}
        try:
            response = requests.get(
                url,
                params={"id": attachment_id},
                auth=(self.user_name, self.access_key),
                timeout=30,
            )
            if response.status_code != 200:
                return {}
            result = response.json()
        except (requests.RequestException, ValueError):
            return {}
        if not result.get("success") or not result.get("result"):
            return {}
        file_data = result["result"][0]
        return {
            "filename": file_data.get("filename"),
            "filetype": file_data.get("filetype"),
            "filesize": file_data.get("filesize"),
            "content": file_data.get("filecontents"),
        }

    def _get_vtiger_document_details(self, res, session_name):
        if not res.get("id") or self._get_vtiger_document_attachment_id(res):
            return res
        result = self._execute_vtiger_document_retrieve(
            self, res.get("id"), session_name
        )
        if not result.get("success") or not result.get("result"):
            return res
        detailed_res = dict(res)
        detailed_res.update(result["result"])
        return detailed_res

    def _get_vtiger_document_fallback_content(self, res, name):
        url = res.get("url") or self._get_vtiger_document_url(res.get("id"))
        content_lines = []
        if url:
            content_lines.append(
                "VTiger URL: %s" % self._normalize_vtiger_document_url(url)
            )
        if res.get("notecontent"):
            content_lines.append("")
            content_lines.append(res.get("notecontent"))
        content = "\n".join(content_lines) or name
        return base64.b64encode(content.encode("utf-8")).decode("ascii")

    def _prepare_vtiger_document_values(self, res, session_name, folder_cache):
        res = self._get_vtiger_document_details(res, session_name)
        file_data = self._fetch_vtiger_document_file(res)
        name = (
            file_data.get("filename")
            or res.get("filename")
            or res.get("notes_title")
            or res.get("id")
        )
        folder = self._get_or_create_vtiger_document_folder(
            res.get("folderid"), session_name, folder_cache
        )
        content = file_data.get(
            "content"
        ) or self._get_vtiger_document_fallback_content(res, name)
        return {
            "name": name,
            "directory_id": folder.id if folder else False,
            "content": content,
            "vtiger_document_no": res.get("note_no"),
            "vtiger_filename": file_data.get("filename") or res.get("filename"),
            "vtiger_filesize": self._vtiger_int(
                file_data.get("filesize") or res.get("filesize")
            ),
            "vtiger_filetype": file_data.get("filetype") or res.get("filetype"),
            "vtiger_folder_id": res.get("folderid"),
            "vtiger_document_source": res.get("document_source"),
            "vtiger_document_type": res.get("document_type"),
            "vtiger_notecontent": res.get("notecontent"),
            "vtiger_createdtime": self._to_vtiger_datetime(res.get("createdtime")),
            "vtiger_modifiedtime": self._to_vtiger_datetime(res.get("modifiedtime")),
        }

    def _get_or_create_vtiger_dms_storage(self):
        storage_obj = self.env["dms.storage"].sudo()
        storage = storage_obj.search(
            [
                ("name", "=", "VTiger Documents"),
                ("company_id", "in", [False, self.id]),
            ],
            limit=1,
        )
        if storage:
            return storage
        return storage_obj.create(
            {
                "name": "VTiger Documents",
                "save_type": "database",
                "company_id": self.id,
            }
        )

    def _get_or_create_vtiger_dms_access_group(self):
        access_group_obj = self.env["dms.access.group"].sudo()
        access_group = access_group_obj.search(
            [("name", "=", "VTiger Documents Users")],
            limit=1,
        )
        dms_user_group = self.env.ref("dms.group_dms_user", raise_if_not_found=False)
        values = {
            "perm_create": True,
            "perm_write": True,
            "perm_unlink": True,
        }
        if dms_user_group:
            values["group_ids"] = [(4, dms_user_group.id)]
        if access_group:
            access_group.write(values)
            return access_group
        values["name"] = "VTiger Documents Users"
        return access_group_obj.create(values)

    def _get_or_create_vtiger_root_directory(self):
        storage = self._get_or_create_vtiger_dms_storage()
        access_group = self._get_or_create_vtiger_dms_access_group()
        directory_obj = self.env["dms.directory"].sudo()
        directory = directory_obj.search(
            [
                ("name", "=", "VTiger Documents"),
                ("is_root_directory", "=", True),
                ("storage_id", "=", storage.id),
            ],
            limit=1,
        )
        if directory:
            if access_group and access_group not in directory.group_ids:
                directory.write({"group_ids": [(4, access_group.id)]})
            return directory
        values = {
            "name": "VTiger Documents",
            "is_root_directory": True,
            "storage_id": storage.id,
        }
        if access_group:
            values["group_ids"] = [(4, access_group.id)]
        return directory_obj.create(values)

    def _ensure_vtiger_dms_directory_access(self, directory):
        access_group = self._get_or_create_vtiger_dms_access_group()
        if not directory or not access_group:
            return
        directories = directory | directory.parent_id
        for directory_item in directories:
            if access_group not in directory_item.group_ids:
                directory_item.write({"group_ids": [(4, access_group.id)]})

    def _get_vtiger_document_storage_domain(self):
        storage = self._get_or_create_vtiger_dms_storage()
        return [("storage_id", "=", storage.id)]

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
            return self._get_or_create_vtiger_root_directory()
        if vtiger_folder_id in folder_cache:
            return folder_cache[vtiger_folder_id]
        folder_obj = self.env["dms.directory"].sudo()
        folder = folder_obj.search(
            [
                ("vtiger_id", "=", vtiger_folder_id),
                ("storage_id.company_id", "in", [False, self.id]),
            ],
            limit=1,
        )
        folder_name = self._get_vtiger_document_folder_name(
            vtiger_folder_id, session_name
        )
        if folder:
            if folder_name and folder.name != folder_name:
                folder.write({"name": folder_name})
            self._ensure_vtiger_dms_directory_access(folder)
            folder_cache[vtiger_folder_id] = folder
            return folder
        folder = folder_obj.create(
            {
                "name": folder_name or vtiger_folder_id,
                "parent_id": self._get_or_create_vtiger_root_directory().id,
                "group_ids": [
                    (4, self._get_or_create_vtiger_dms_access_group().id)
                ],
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
        document_obj = self.env["dms.file"].sudo()
        storage_domain = self._get_vtiger_document_storage_domain()
        document = document_obj.search(
            [("vtiger_id", "=", vtiger_id)] + storage_domain,
            limit=1,
        )
        if not document and vals.get("vtiger_document_no"):
            document = document_obj.search(
                [
                    ("vtiger_document_no", "=", vals["vtiger_document_no"]),
                    ("vtiger_id", "=", False),
                ]
                + storage_domain,
                limit=1,
            )
        if not document and vals.get("name"):
            document = document_obj.search(
                [
                    ("name", "=ilike", vals["name"]),
                    ("vtiger_id", "=", False),
                ]
                + storage_domain,
                limit=1,
            )
        if document:
            if not document.vtiger_id:
                vals["vtiger_id"] = vtiger_id
            document.write(vals)
        else:
            vals["vtiger_id"] = vtiger_id
            document_obj.create(vals)

    def _repair_vtiger_document_folders(self, session_name):
        document_obj = self.env["dms.file"].sudo()
        documents = document_obj.search(
            [
                ("vtiger_id", "!=", False),
                ("vtiger_folder_id", "!=", False),
                ("directory_id", "=", False),
                ("storage_id.company_id", "in", [False, self.id]),
            ]
        )
        folder_cache = {}
        for document in documents:
            folder = self._get_or_create_vtiger_document_folder(
                document.vtiger_folder_id, session_name, folder_cache
            )
            if folder:
                document.write({"directory_id": folder.id})

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
