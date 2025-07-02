{
    'name': 'Highlight CRM Based on Due Date',
    'version': '17.0.0.1',
    'category': 'Sales',
    'license': 'LGPL-3',
    'summary': 'In a CRM system, implementing a Kanban view based on due dates allows for visualizing and managing '
               'tasks or deals according to their deadlines.',
    'description': 'In a CRM systems Kanban view, due dates are integrated to visually highlight task deadlines. '
                   'This allows users to quickly identify upcoming and overdue tasks, prioritize their workload,'
                   ' and take proactive steps to meet deadlines effectively.',
    'author': 'AppsComp Widgets Pvt Ltd',
    'website': 'https://www.appscomp.com',
    'depends': ['base', 'crm'],
    'data': [
        'views/crm_view.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    "images": ['static/description/banner.png'],
   # "images": ['static/description/banner.gif'],

}
