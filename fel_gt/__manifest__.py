# -*- encoding: utf-8 -*-

{
    'name': 'FEL Guatemala',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Localizations/EDI',
    'description': """ Campos y funciones base para la facturación electrónica en Guatemala """,
    'author': 'Rodrigo Fernandez',
    'website': 'http://aquih.com/',
    'license': 'AGPL-3',
    'depends': ['l10n_gt_extra', 'stock'],
    'data': [
        'views/account_view.xml',
        'views/partner_view.xml',
        'views/report_delivery.xml',
    ],
    'demo': [],
    'installable': True,
}
