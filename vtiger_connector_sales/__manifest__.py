# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

{
    'name': 'VTiger Sales Connector',
    'version': '12.0.1.0.0',
    'category': 'Sales',
    'license': 'AGPL-3',
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'maintainer': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'https://www.serpentcs.com',
    'depends': ['sale_management',
                'vtiger_connector_products',
                'vtiger_connector_partner',
                'vtiger_connector_crm'],
    'data': ['views/res_company_view.xml',
             'views/sale_view.xml'],
    'installable': True,
}
