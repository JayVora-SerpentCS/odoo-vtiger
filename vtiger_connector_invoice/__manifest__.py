# See LICENSE file for full copyright and licensing details.

{
    'name': 'VTiger Invoice Connector',
    'version': '13.0.1.0.0',
    'category': 'Invoicing',
    'license': 'AGPL-3',
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'maintainer': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'https://www.serpentcs.com',
    'depends': ['account',
                'vtiger_connector_products',
                'vtiger_connector_partner',
                ],
    'data': ['views/res_company_view.xml',
             'views/invoice_view.xml'],
    'installable': True,
    'images': ['static/description/banner.jpg'],
}
