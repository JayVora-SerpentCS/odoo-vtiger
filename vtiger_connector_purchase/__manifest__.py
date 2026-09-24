# See LICENSE file for full copyright and licensing details.

{
    "name": (
        "VTiger Purchase Connector | Odoo VTiger Purchase Connector | "
        "VTiger Purchase Integration with Odoo"
    ),
    "version": "19.0.1.0.0",
    "summary": """
        Advanced Vtiger Purchase Connector | Vtiger Purchase Connector |
        Vtiger Vendor Connector | Vtiger Vendor Integration |
        Vtiger Purchase Integration | Vtiger Vendor Connector Software |
        Vtiger Purchase Connector Software |
        Vtiger Vendor Sync Software | Vtiger Purchase Sync ERP |
        Vtiger Vendor Sync ERP | Odoo Vtiger Purchase Connector |
        Odoo Vtiger Vendor Connector | Odoo Vtiger Purchase Integration |
        Odoo Vtiger Vendor Integration |
        Odoo Vtiger Vendor Sync Software |
        Odoo Vtiger Purchase Connector Module |
        Odoo Vtiger Vendor Integration Software |
        Vtiger Vendor Sync | Vtiger Purchase Sync |
        Advanced Vtiger Vendor Integration |
        VTiger Purchase Integration with Odoo
        """,
    "category": "Purchases",
    "sequence": 1,
    "license": "AGPL-3",
    "author": "Serpent Consulting Services Pvt. Ltd.",
    "maintainer": "Serpent Consulting Services Pvt. Ltd.",
    "website": "https://www.serpentcs.com",
    "depends": [
        "purchase",
        "vtiger_connector_products",
        "vtiger_connector_partner",
    ],
    "data": ["views/res_company_view.xml", "views/purchase_view.xml"],
    "installable": True,
    "images": [
        "static/description/vtiger_purchase_connector_odoo_vtiger_purchase_"
        "connector_vtiger_purchase_integration_with_odoo_product_banner.png"
    ],
}
