# -*- coding: utf-8 -*-
{
    'name': "agro",
    'description' : "agro",
    'depends': ['base', 'stock', 'product_expiry', 'mail', 'sale_stock'],

    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/report_wizard_view.xml',
        'reports/agro_report.xml'
    ],
}