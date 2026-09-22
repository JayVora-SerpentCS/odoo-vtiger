# See LICENSE file for full copyright and licensing details.

{
    "name": (
        "VTiger Sales Connector | Odoo VTiger Sales Connector | "
        "VTiger Sales Integration with Odoo"
    ),
    "version": "18.0.1.0.0",
    "summary": """
        Advanced Vtiger Sales Connector | Vtiger Sales Connector |
        Vtiger Sales Order Connector | Vtiger Sales Order Integration |
        Vtiger Sales Integration | Vtiger Sales Order Connector Software |
        Vtiger Sales Connector Software |
        Vtiger Sales Order Sync Software | Vtiger Sales Sync ERP |
        Vtiger Sales Order Sync ERP | Odoo Vtiger Sales Connector |
        Odoo Vtiger Sales Order Connector | Odoo Vtiger Sales Integration |
        Odoo Vtiger Sales Order Integration |
        Odoo Vtiger Sales Order Sync Software |
        Odoo Vtiger Sales Connector Module |
        Odoo Vtiger Sales Order Integration Software |
        Vtiger Sales Order Sync | Vtiger Sales Sync |
        Advanced Vtiger Sales Order Integration |
        VTiger Sales Integration with Odoo
        """,
    "category": "Sales",
    "sequence": 1,
    "license": "AGPL-3",
    "author": "Serpent Consulting Services Pvt. Ltd.",
    "maintainer": "Serpent Consulting Services Pvt. Ltd.",
    "website": "https://www.serpentcs.com",
    "depends": [
        "sale",
        "sale_management",
        "vtiger_connector_products",
        "vtiger_connector_partner",
        "vtiger_connector_crm",
    ],
    "data": ["views/res_company_view.xml", "views/sale_view.xml"],
    "installable": True,
    "images": [
        "static/description/vtiger_sales_connector_odoo_vtiger_sales_"
        "connector_vtiger_sales_integration_with_odoo_product_banner.png"
    ],
}
