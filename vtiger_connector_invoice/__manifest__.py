# See LICENSE file for full copyright and licensing details.

{
    "name": "VTiger Invoice Connector | Odoo VTiger Invoice Connector | VTiger Invoice Integration with Odoo",
    "version": "18.0.1.0.0",
    'summary': '''
        Advanced Vtiger Invoice Connector | Vtiger Invoice Connector | Invoice Sync Connector | Invoice Sync Integration |
        Vtiger Invoice Integration | Invoice Sync Connector Software | Vtiger Invoice Connector Software |
        Invoice Sync Sync Software | Vtiger Invoice Sync ERP | Invoice Sync Sync ERP | Odoo Vtiger Invoice Connector |
        Odoo Invoice Sync Connector | Odoo Vtiger Invoice Integration | Odoo Invoice Sync Integration |
        Odoo Invoice Sync Sync Software | Odoo Vtiger Invoice Connector Module | Odoo Invoice Sync Integration Software |
        Invoice Sync Sync | Vtiger Invoice Sync | Advanced Invoice Sync Integration | Vtiger Invoice Integration with Odoo
        ''',
    "category": "Invoicing",
    "license": "AGPL-3",
    "author": "Serpent Consulting Services Pvt. Ltd.",
    "maintainer": "Serpent Consulting Services Pvt. Ltd.",
    "website": "https://www.serpentcs.com",
    "depends": [
        "account",
        "vtiger_connector_products",
        "vtiger_connector_partner",
    ],
    "data": ["views/res_company_view.xml", "views/invoice_view.xml"],
    "installable": True,
    "images": ["static/description/vtiger_invoice_connector_odoo_vtiger_invoice_connector_vtiger_invoice_integration_with_odoo_product_banner.png"],
}
