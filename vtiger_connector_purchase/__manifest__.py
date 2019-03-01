# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
{
    'name': 'Purchase VTiger Integration',
    'version': '10.0.1.0.0',
    'summary': 'Purchase VTiger Integration',
    'description': """
        Purchase VTiger Integration""",
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'https://www.serpentcs.com',
    'category': 'Purchases',
    'license': 'AGPL-3',
    'depends': ['purchase',
                'vtiger_connector_products',
                'vtiger_connector_partner'],
    'data': ['views/res_company_view.xml',
             'views/purchase_view.xml'],
    'installable': True,
}
