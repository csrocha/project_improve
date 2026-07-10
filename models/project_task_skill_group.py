# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProjectTaskSkillGroup(models.Model):
    _name = 'project.task.skill.group'
    _description = 'Puesto adicional de una tarea, cubierto en simultáneo por skill'
    _order = 'sequence, id'

    task_id = fields.Many2one(
        'project.task', string='Tarea', required=True, ondelete='cascade', index=True,
    )
    sequence = fields.Integer(default=10)
    required_skill_ids = fields.Many2many(
        'hr.skill', string='Skills requeridas',
        help='Skills que debe tener, todas a la vez, cualquier candidato de '
             'este puesto. A diferencia de required_skill_ids de la tarea '
             '(el puesto principal, siempre presente), cada grupo acá es un '
             'puesto adicional que se cubre en simultáneo con el principal '
             '— no un "rol" con nombre fijo, sino otro filtro de skills.',
    )
    resource_pool_ids = fields.Many2many(
        'res.users', 'project_task_skill_group_resource_pool_rel',
        'group_id', 'user_id', string='Pool de candidatos',
        compute='_compute_resource_pool_ids', store=True, readonly=False,
        help='Empleados candidatos a este puesto. Se recalcula cuando '
             'cambian required_skill_ids o la lista de candidatos del '
             'proyecto, pero se puede ajustar a mano; el ajuste manual se '
             'preserva hasta el próximo recálculo.',
    )

    @api.constrains('required_skill_ids')
    def _check_required_skill_ids(self):
        for group in self:
            if not group.required_skill_ids:
                raise ValidationError(_(
                    'Todo puesto adicional necesita al menos una skill '
                    'requerida. Si no hace falta filtrar por skill, no haga '
                    'falta un grupo aparte: el pool de la tarea '
                    '(resource_pool_ids/user_ids) ya cubre ese puesto.'
                ))

    @api.depends('required_skill_ids', 'task_id.project_id.candidate_user_ids')
    def _compute_resource_pool_ids(self):
        for group in self:
            if not group.required_skill_ids:
                group.resource_pool_ids = False
                continue
            required_ids = set(group.required_skill_ids.ids)
            employees = self.env['hr.employee'].sudo().search([
                ('skill_ids', 'in', group.required_skill_ids.ids),
            ]).filtered(lambda e: required_ids <= set(e.skill_ids.ids))
            candidates = group.task_id.project_id.candidate_user_ids
            if candidates:
                employees = employees.filtered(lambda e: e.user_id in candidates)
            group.resource_pool_ids = employees.mapped('user_id')
