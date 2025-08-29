# -*- coding: utf-8 -*-
{
    'name': "Comprobantes de Nómina LOGYCA",

    'summary': """
        Módulo de nómina para la localización colombiana | Liquidación de Nómina""",

    'description': """
        Módulo de nómina para la localización colombiana | Liquidación de Nómina
    """,

    'author': "Lorena Torres",
    
    'category': 'Human Resources',
    "version": "1.0.0",
    'license': 'OPL-1',
    'depends': ['base','hr','hr_payroll','hr_holidays','web'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/actions_voucher_sending.xml',
        'views/hr_employee_view.xml',
    ],
    
}

