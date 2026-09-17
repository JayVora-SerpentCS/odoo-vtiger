# See LICENSE file for full copyright and licensing details.

{
    "name": (
        "VTiger Base Connector | Vtiger Integration with Odoo | "
        "Odoo Vtiger Connector"
    ),
    "version": "18.0.1.0.0",
    "summary": """
        Advanced Vtiger Base Connector | Vtiger Base Connector |
        Vtiger Odoo Connector | Vtiger Odoo Integration |
        Vtiger Base Integration | Vtiger Odoo Connector Software |
        Vtiger Base Connector Software | Vtiger Odoo Sync Software |
        Vtiger Base Sync ERP | Vtiger Odoo Sync ERP |
        Odoo Vtiger Base Connector | Odoo Vtiger Odoo Connector |
        Odoo Vtiger Base Integration | Odoo Vtiger Odoo Integration |
        Odoo Vtiger Odoo Sync Software |
        Odoo Vtiger Base Connector Module |
        Odoo Vtiger Odoo Integration Software | Vtiger Odoo Sync |
        Vtiger Base Sync | Advanced Vtiger Odoo Integration |
        Vtiger Integration with Odoo | Odoo Vtiger Connector
        """,
    "category": "Base Module",
    "license": "AGPL-3",
    "author": "Serpent Consulting Services Pvt. Ltd.",
    "maintainer": "Serpent Consulting Services Pvt. Ltd.",
    "website": "https://www.serpentcs.com",
    "depends": ["base"],
    "data": ["data/vtiger_connector_base_data.xml", "views/res_company_view.xml"],
    "installable": True,
    "assets": {
        "web.assets_backend": [
            "vtiger_connector_base/static/src/css/vtiger_base.css",
        ]
    },
    "images": [
        "static/description/vtiger_base_connector_vtiger_integration_with_odoo_"
        "odoo_vtiger_connector_product_banner.png"
    ],
}
