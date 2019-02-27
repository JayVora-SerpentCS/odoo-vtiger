# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

{
    'name': 'VTiger Base Connector Purchase',
    'version': '11.0.1.0.0',
    'category': '',
    'license': 'AGPL-3',
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'maintainer': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'https://www.serpentcs.com',
    'depends': [
        'vtiger_connector_products',
        'vtiger_connector_partner',
        'purchase',
    ],
    'data': [
        'views/res_company_view.xml',
        'views/purchase_view.xml',
    ],
    'installable': True,
}
