# See LICENSE file for full copyright and licensing details.

{
    'name': 'VTiger Purchase Connector',
    'version': '13.0.1.0.0',
    'category': 'Purchases',
    'license': 'AGPL-3',
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'maintainer': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'https://www.serpentcs.com',
    'depends': ['purchase',
                'vtiger_connector_products',
                'vtiger_connector_partner'],
    'data': ['views/res_company_view.xml',
             'views/purchase_view.xml'],
    'installable': True,
}
