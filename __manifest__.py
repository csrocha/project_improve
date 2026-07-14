# -*- coding: utf-8 -*-
{
    'name': "Project Improve",
    'summary': "Campos genéricos de project.task (blocked, is_critical_path) sin motor de scheduling",
    'version': '17.0.1.1.3',
    'category': 'Project',
    'author': "Cristian S. Rocha <csrocha@gmail.com>",
    'website': "https://github.com/csrocha/project_improve",
    'license': 'OPL-1',
    'depends': ['project', 'hr_skills'],
    'data': [
        'security/ir.model.access.csv',
        'views/project_project_views.xml',
        'views/project_task_views.xml',
    ],
    'installable': True,
    'application': False,
}
