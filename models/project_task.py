# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    required_skill_ids = fields.Many2many(
        'hr.skill', string='Skills requeridas',
        help='Skills necesarias para hacer esta tarea. Si se completa, '
             'resource_pool_ids se recalcula automáticamente a partir de los '
             'empleados que las tengan todas.',
    )
    resource_pool_ids = fields.Many2many(
        'res.users', 'project_task_resource_pool_rel', 'task_id', 'user_id',
        string='Pool de candidatos',
        compute='_compute_resource_pool_ids', store=True, readonly=False,
        help='Empleados candidatos a hacer esta tarea. Se recalcula cuando '
             'cambian required_skill_ids o la lista de candidatos del '
             'proyecto, pero se puede ajustar a mano; el ajuste manual se '
             'preserva hasta el próximo recálculo.',
    )
    blocked = fields.Boolean(
        string='Bloqueada', tracking=True,
        help='Impedimento temporal que impide continuar el trabajo. No '
             'reemplaza stage_id ni state: puede coexistir con cualquier '
             'etapa/estado activo. El motivo se registra donde cada addon '
             'consumidor decida (chatter, parte de horas, etc.), no en '
             'este campo.',
    )
    is_critical_path = fields.Boolean(
        string='Camino crítico',
        help='Campo plano, sin cómputo propio. Si insight_project (u otro '
             'motor de scheduling) está instalado, ese addon le agrega el '
             'compute correspondiente.',
    )
    @api.depends('required_skill_ids', 'project_id.candidate_user_ids')
    def _compute_resource_pool_ids(self):
        for task in self:
            if not task.required_skill_ids:
                task.resource_pool_ids = task.user_ids
                continue
            required_ids = set(task.required_skill_ids.ids)
            employees = self.env['hr.employee'].sudo().search([
                ('skill_ids', 'in', task.required_skill_ids.ids),
            ]).filtered(lambda e: required_ids <= set(e.skill_ids.ids))
            candidates = task.project_id.candidate_user_ids
            if candidates:
                employees = employees.filtered(lambda e: e.user_id in candidates)
            task.resource_pool_ids = employees.mapped('user_id')
