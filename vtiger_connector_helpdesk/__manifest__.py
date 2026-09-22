# See LICENSE file for full copyright and licensing details.

{
    "name": (
        "VTiger HelpDesk Connector | Odoo VTiger Ticket Connector | "
        "VTiger HelpDesk Integration with Odoo"
    ),
    "version": "18.0.1.0.0",
    "summary": (
        "Advanced Vtiger Helpdesk Connector | Vtiger Helpdesk Connector | "
        "Vtiger Ticket Connector | Vtiger Ticket Integration | "
        "Vtiger Helpdesk Integration | Vtiger Ticket Connector Software | "
        "Vtiger Helpdesk Connector Software | Vtiger Ticket Sync Software | "
        "Vtiger Helpdesk Sync ERP | Vtiger Ticket Sync ERP | "
        "Odoo Vtiger Helpdesk Connector | Odoo Vtiger Ticket Connector | "
        "Odoo Vtiger Helpdesk Integration | Odoo Vtiger Ticket Integration | "
        "Odoo Vtiger Ticket Sync Software | "
        "Odoo Vtiger Helpdesk Connector Module | "
        "Odoo Vtiger Ticket Integration Software | Vtiger Ticket Sync | "
        "Vtiger Helpdesk Sync | Advanced Vtiger Ticket Integration | "
        "VTiger HelpDesk Integration with Odoo"
    ),
    "category": "Services/Helpdesk",
    "sequence": 1,
    "license": "AGPL-3",
    "author": "Serpent Consulting Services Pvt. Ltd.",
    "maintainer": "Serpent Consulting Services Pvt. Ltd.",
    "website": "https://www.serpentcs.com",
    "depends": ["helpdesk_mgmt", "vtiger_connector_partner"],
    "data": [
        "views/res_company_view.xml",
        "views/helpdesk_ticket_view.xml",
    ],
    "images": [
        "static/description/vtiger_helpdesk_connector_odoo_vtiger_ticket_connector_"
        "vtiger_helpdesk_integration_with_odoo_product_banner.png"
    ],
    "installable": True,
}
