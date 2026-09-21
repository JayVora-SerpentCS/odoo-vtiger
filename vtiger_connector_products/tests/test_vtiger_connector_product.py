from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("scs_custom_vtiger_test")
class TestVtigerProduct(TransactionCase):
    def test_vtiger_product(self):
        vtiger_service_product_dict = {
            "success": True,
            "vtiger_type": "Service",
            "result": [
                {
                    "servicename": "service producttttttttttt",
                    "discontinued": "1",
                    "servicecategory": "Installation",
                    "assigned_user_id": "19x1",
                    "service_usageunit": "Hours",
                    "qty_per_unit": "",
                    "sales_start_date": "",
                    "sales_end_date": "",
                    "start_date": "",
                    "expiry_date": "",
                    "website": "",
                    "service_no": "SER7",
                    "createdtime": "2024-09-30 06:40:37",
                    "modifiedtime": "2024-09-30 10:50:58",
                    "modifiedby": "19x1",
                    "created_user_id": "19x1",
                    "source": "CRM",
                    "starred": "0",
                    "tags": "",
                    "record_currency_id": "21x2",
                    "record_conversion_rate": "1.00000",
                    "unit_price": "50.00000000",
                    "commissionrate": "",
                    "taxclass": "",
                    "purchase_cost": "",
                    "purchase_cost_currency_value": "",
                    "billing_type": "One time",
                    "description": "service descriptionnnnn",
                    "id": "25x502",
                    "isclosed": "0",
                    "record_currency_symbol": "₹",
                }
            ],
        }

        if vtiger_service_product_dict.get("success"):
            service_product_result = vtiger_service_product_dict.get("result")[0]

            if vtiger_service_product_dict.get("vtiger_type") == "Service":
                self.env["product.template"].create(
                    {
                        "name": service_product_result.get("servicename"),
                        "detailed_type": "service",
                        "sale_ok": True,
                        "purchase_ok": True,
                        "list_price": service_product_result.get("unit_price"),
                        "standard_price": service_product_result.get("purchase_cost"),
                        "description_sale": service_product_result.get("description"),
                        "vtiger_id": service_product_result.get("id"),
                        "purchase_line_warn": "no-message",
                    }
                )

        # Sample product data
        vtiger_product_dict = {
            "success": True,
            "vtiger_type": "Product",
            "result": [
                {
                    "productname": "Sep30 Test Product",
                    "productcode": "",
                    "product_type": "Solo",
                    "discontinued": "1",
                    "productcategory": "Hardware",
                    "vendor_id": "11x499",
                    "manufacturer": "AltvetPet Inc.",
                    "sales_start_date": "",
                    "sales_end_date": "2024-09-25",
                    "start_date": "",
                    "expiry_date": "2024-10-01",
                    "serial_no": "",
                    "mfr_part_no": "",
                    "vendor_part_no": "",
                    "website": "",
                    "glacct": "",
                    "productsheet": "",
                    "createdtime": "2024-09-30 07:27:17",
                    "modifiedtime": "2024-09-30 07:27:17",
                    "product_no": "PRO15",
                    "modifiedby": "19x1",
                    "created_user_id": "19x1",
                    "source": "CRM",
                    "starred": "0",
                    "tags": "",
                    "record_currency_id": "21x2",
                    "record_conversion_rate": "1.00000",
                    "item_barcode": "",
                    "hsn_code": "",
                    "unit_price": "50.00000000",
                    "commissionrate": "",
                    "taxclass": "",
                    "purchase_cost": "",
                    "purchase_cost_currency_value": "",
                    "billing_type": "One time",
                    "usageunit": "",
                    "qty_per_unit": "10.00",
                    "qtyinstock": "100.000",
                    "reorderlevel": "0",
                    "assigned_user_id": "19x1",
                    "qtyindemand": "",
                    "defect_qtyinstock": "0.000",
                    "reorder_qty": "0.000",
                    "availablestock": "100.000",
                    "committedstock": "0.000",
                    "incomingstock": "0.000",
                    "imagename": "",
                    "description": "SEP TEST PRODUCT",
                    "id": "6x503",
                    "isclosed": "0",
                    "record_currency_symbol": "₹",
                }
            ],
        }

        if vtiger_product_dict.get("success"):
            product_result = vtiger_product_dict.get("result")[0]

            # Create Consumable Product
            if vtiger_product_dict.get("vtiger_type") == "Product":
                self.env["product.template"].create(
                    {
                        "name": product_result.get("productname"),
                        "detailed_type": "consu",
                        "sale_ok": True,
                        "purchase_ok": True,
                        "default_code": product_result.get("serial_no"),
                        "list_price": product_result.get("unit_price"),
                        "standard_price": product_result.get("purchase_cost"),
                        "description_sale": product_result.get("description"),
                        "vtiger_id": product_result.get("id"),
                        "purchase_line_warn": "no-message",
                    }
                )
