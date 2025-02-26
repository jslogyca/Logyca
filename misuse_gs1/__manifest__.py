{
    'name': 'Misuse GS1 Log',
    'version': '15.0.1.0.0',
    'summary': 'Almacena la trazabilidad del mal uso del sistema GS1',
    'author': 'LOGYCA / SERVICIOS',
    'depends': ['contacts'],
    'data': [
        'security/ir.model.access.csv',
        'views/misuse_gs1_log_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'Other proprietary'
}
