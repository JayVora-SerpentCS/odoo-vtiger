{
    'name': 'Products VTiger Integration Products',
    'version': '11.0.1.0.0',
    'summary': 'Products VTiger Integration',
    'description': """
        Products VTiger Integration""",
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'https://www.serpentcs.com',
    'category': '',
    'depends': [
        'vtiger_connector_base',
        'product',
    ],
    'data': [
        'views/res_company_view.xml',
        'views/product_template_view.xml',
    ],
    'installable': True,
}
