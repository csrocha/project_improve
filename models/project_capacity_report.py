# -*- coding: utf-8 -*-
from collections import defaultdict
from datetime import timedelta

from odoo import api, fields, models


class ProjectCapacityReportWizard(models.TransientModel):
    _name = 'project.capacity.report.wizard'
    _description = 'Capacidad agregada por skill entre todos los proyectos en progreso'

    horizon_weeks = fields.Integer(
        default=4, required=True,
        help='Ventana hacia adelante desde hoy. "Comprometido" = horas de '
             'tareas abiertas con vencimiento dentro de la ventana; '
             '"disponible" = calendario laboral de cada empleado candidato '
             'en esa misma ventana, descontando lo que ya tiene asignado.',
    )
    line_ids = fields.One2many(
        'project.capacity.report.line', 'wizard_id', string='Resultado', readonly=True,
    )

    def action_compute(self):
        self.ensure_one()
        self.line_ids.unlink()
        now = fields.Datetime.now()
        horizon_end = now + timedelta(weeks=self.horizon_weeks)

        open_tasks = self.env['project.task'].search([
            ('project_id.state', '=', 'progress'),
            ('state', 'not in', ['1_done', '1_canceled']),
            ('child_ids', '=', False),
            ('date_deadline', '>=', fields.Datetime.to_string(now)),
            ('date_deadline', '<=', fields.Datetime.to_string(horizon_end)),
        ])

        committed_by_skill = defaultdict(float)
        # Horas que cada usuario YA tiene asignadas (task.user_ids real, no
        # el pool de candidatos) — se descuenta de su calendario disponible
        # sin importar para qué skill se cuenten esas horas.
        committed_by_user = defaultdict(float)
        for task in open_tasks:
            skills = task.required_skill_ids
            if skills:
                share = task.allocated_hours / len(skills)
                for skill in skills:
                    committed_by_skill[skill] += share
            # Puestos adicionales: horas EN SIMULTÁNEO con el puesto
            # principal, no se reparten con él (mismo criterio que
            # insight_project._tjp_allocate para exportar a TJ3).
            for group in task.extra_skill_group_ids:
                group_share = task.allocated_hours / len(group.required_skill_ids)
                for skill in group.required_skill_ids:
                    committed_by_skill[skill] += group_share
            for user in task.user_ids:
                committed_by_user[user.id] += task.allocated_hours

        default_calendar = self.env.company.resource_calendar_id
        for skill, committed_hours in committed_by_skill.items():
            employees = self.env['hr.employee'].sudo().search([
                ('skill_ids', 'in', skill.id),
            ])
            available_hours = 0.0
            for employee in employees:
                calendar = employee.resource_calendar_id or default_calendar
                if calendar:
                    calendar_hours = calendar.get_work_hours_count(now, horizon_end)
                else:
                    calendar_hours = 40.0 * self.horizon_weeks
                already_committed = committed_by_user.get(employee.user_id.id, 0.0)
                available_hours += max(0.0, calendar_hours - already_committed)
            self.env['project.capacity.report.line'].create({
                'wizard_id': self.id,
                'skill_id': skill.id,
                'committed_hours': committed_hours,
                'available_hours': available_hours,
            })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'project.capacity.report.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }


class ProjectCapacityReportLine(models.TransientModel):
    _name = 'project.capacity.report.line'
    _description = 'Línea de resultado del reporte de capacidad agregada'
    _order = 'gap_hours'

    wizard_id = fields.Many2one('project.capacity.report.wizard', ondelete='cascade')
    skill_id = fields.Many2one('hr.skill', string='Skill', required=True)
    committed_hours = fields.Float(string='Comprometido (h)')
    available_hours = fields.Float(string='Disponible (h)')
    gap_hours = fields.Float(
        string='Brecha (h)', compute='_compute_gap_hours', store=True,
        help='Disponible - comprometido. Negativo = déficit (más '
             'comprometido que disponible en la ventana elegida).',
    )

    @api.depends('committed_hours', 'available_hours')
    def _compute_gap_hours(self):
        for line in self:
            line.gap_hours = line.available_hours - line.committed_hours
