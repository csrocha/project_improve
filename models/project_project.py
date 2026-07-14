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
    state = fields.Selection(
        [
            ('draft', 'Borrador'),
            ('evaluation', 'En evaluación'),
            ('progress', 'En progreso'),
            ('done', 'Finalizado'),
        ],
        string='Estado de planificación', default='draft', required=True,
        tracking=True,
        help='Ciclo de vida del proyecto para scheduling de portfolio '
             '(distinto de project.project.stage_id, el Kanban de etapas '
             'nativo de Proyectos, y de project.task.stage_id/state, el '
             'Kanban y el estado de tareas). "Borrador": el '
             'proyecto se planifica aislado, sin competir por recursos con '
             'otros proyectos. "En evaluación": se recalcula junto con los '
             'proyectos "En progreso" para medir el impacto real de '
             'aceptarlo, pero sin modificar el schedule ya comprometido de '
             'esos proyectos. "En progreso": comparte pool de recursos y '
             'replanificación combinada con todos los demás proyectos en '
             'este mismo estado. "Finalizado": sale del pool combinado, ya '
             'no participa en futuras corridas de portfolio.',
    )
    resource_priority = fields.Integer(
        string='Prioridad de recursos', default=10,
        help='Campo sin cómputo propio: solo lo usa el motor de scheduling '
             'de insight_project para desempatar cuándo un mismo recurso es '
             'candidato en más de un proyecto a la vez. Mayor valor = mayor '
             'prioridad.',
    )

    def action_evaluate(self):
        self.ensure_one()
        self.state = 'evaluation'

    def action_start(self):
        self.ensure_one()
        self.state = 'progress'

    def action_discard(self):
        self.ensure_one()
        self.state = 'draft'

    def action_finish(self):
        self.ensure_one()
        self.state = 'done'

    def action_reevaluate(self):
        self.ensure_one()
        self.state = 'evaluation'
