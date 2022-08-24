# See LICENSE file for full copyright and licensing details.

{
    'name': 'VTiger Base Connector',
    'version': '13.0.1.0.0',
    'category': 'Base Module',
    'license': 'AGPL-3',
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'maintainer': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'https://www.serpentcs.com',
    'depends': ['base'],
    'data': ['data/vtiger_connector_base_data.xml',
#              'views/vtiger_templates.xml',
             'views/res_company_view.xml'],
    'installable': True,
    'assets': {
        'web.assets_backend': [
            'vtiger_connector_base/static/src/css/vtiger_base.css',
        ]
        },
    'images': ['static/description/banner.png'],
}
