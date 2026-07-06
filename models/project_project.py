# -*- coding: utf-8 -*-
from odoo import fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    candidate_user_ids = fields.Many2many(
        'res.users', string='Candidatos disponibles',
        help='Empleados que se pueden considerar para la asignación '
             'automática de tareas de este proyecto (via resource_pool_ids). '
             'Vacío = considerar a todos los empleados de la compañía.',
    )
