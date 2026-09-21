from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("scs_custom_vtiger_test")
class TestVtigerProject(TransactionCase):
    def test_vtiger_product(self):
        vtiger_project_dict = {
            "success": True,
            "result": [
                {
                    "projectname": "Sep 30 project",
                    "projectstatus": "New",
                    "linktoaccountscontacts": "3x500",
                    "assigned_user_id": "19x1",
                    "startdate": "2024-09-30",
                    "targetenddate": "2024-09-30",
                    "actualenddate": "2024-09-04",
                    "project_no": "PROJ4",
                    "created_user_id": "19x1",
                    "isconvertedfrompotential": "0",
                    "potentialid": "",
                    "contactid": "",
                    "source": "CRM",
                    "starred": "0",
                    "tags": "",
                    "record_currency_id": "",
                    "record_conversion_rate": "",
                    "isclosed": "0",
                    "targetbudget": "",
                    "projecturl": "",
                    "projectpriority": "high",
                    "progress": "",
                    "createdtime": "2024-09-30 12:09:37",
                    "modifiedtime": "2024-09-30 12:09:37",
                    "modifiedby": "19x1",
                    "description": "This is project description.",
                    "id": "31x504",
                    "record_currency_symbol": None,
                }
            ],
        }

        if vtiger_project_dict.get("success"):
            project_result = vtiger_project_dict.get("result")[0]

            self.env["product.template"].create(
                {
                    "name": project_result.get("projectname"),
                    "vtiger_id": project_result.get("id"),
                }
            )
