# -*- coding: utf-8 -*-
"""Regression tests for project.capacity.report.wizard (Épica 3 del roadmap
de ecosistema): comprometido = allocated_hours de tareas abiertas (hoja, en
proyectos 'progress', con vencimiento dentro de la ventana) repartido entre
required_skill_ids; disponible = calendario laboral de cada empleado
candidato, descontando lo que ya tiene asignado (task.user_ids real, no el
pool de candidatos)."""
from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase

from .test_resource_pool import SkillPoolFixtures


class TestCapacityReport(SkillPoolFixtures, TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.project.state = 'progress'
        # Calendario determinístico: 8h/día lunes a viernes = 40h/semana,
        # sin importar en qué día de la semana caiga "ahora" (una ventana
        # rodante de 7 días siempre contiene los 5 días hábiles una vez).
        cls.calendar = cls.env['resource.calendar'].create({
            'name': 'Capacity Test Calendar',
            'attendance_ids': [
                (5, 0, 0),
                *[(0, 0, {
                    'name': f'Día {i}', 'dayofweek': str(i),
                    'hour_from': 9.0, 'hour_to': 17.0, 'day_period': 'morning',
                }) for i in range(5)],
            ],
        })
        for user in (cls.user_both, cls.user_python_only, cls.user_none):
            user.employee_id.resource_calendar_id = cls.calendar.id

    def _wizard(self, horizon_weeks=1):
        return self.env['project.capacity.report.wizard'].create({
            'horizon_weeks': horizon_weeks,
        })

    def _line(self, wizard, skill):
        return wizard.line_ids.filtered(lambda l: l.skill_id == skill)

    def test_committed_hours_split_evenly_across_required_skills(self):
        self._task(
            name='Full stack', allocated_hours=10.0,
            date_deadline=fields.Datetime.now() + timedelta(days=2),
            required_skill_ids=[(6, 0, (self.skill_python | self.skill_go).ids)],
        )
        wizard = self._wizard()
        wizard.action_compute()
        self.assertEqual(self._line(wizard, self.skill_python).committed_hours, 5.0)
        self.assertEqual(self._line(wizard, self.skill_go).committed_hours, 5.0)

    def test_extra_skill_group_counts_full_hours_not_shared(self):
        task = self._task(
            name='Pair task', allocated_hours=8.0,
            date_deadline=fields.Datetime.now() + timedelta(days=2),
            required_skill_ids=[(6, 0, self.skill_python.ids)],
        )
        self.env['project.task.skill.group'].create({
            'task_id': task.id,
            'required_skill_ids': [(6, 0, self.skill_go.ids)],
        })
        wizard = self._wizard()
        wizard.action_compute()
        self.assertEqual(self._line(wizard, self.skill_python).committed_hours, 8.0)
        self.assertEqual(self._line(wizard, self.skill_go).committed_hours, 8.0)

    def test_task_beyond_horizon_excluded(self):
        self._task(
            name='Fuera de ventana', allocated_hours=10.0,
            date_deadline=fields.Datetime.now() + timedelta(weeks=5),
            required_skill_ids=[(6, 0, self.skill_python.ids)],
        )
        wizard = self._wizard(horizon_weeks=1)
        wizard.action_compute()
        self.assertFalse(self._line(wizard, self.skill_python))

    def test_done_task_excluded(self):
        self._task(
            name='Ya terminada', allocated_hours=10.0,
            date_deadline=fields.Datetime.now() + timedelta(days=1),
            required_skill_ids=[(6, 0, self.skill_python.ids)],
            state='1_done',
        )
        wizard = self._wizard()
        wizard.action_compute()
        self.assertFalse(self._line(wizard, self.skill_python))

    def test_parent_task_with_children_excluded(self):
        parent = self._task(
            name='Padre', allocated_hours=999.0,
            date_deadline=fields.Datetime.now() + timedelta(days=1),
            required_skill_ids=[(6, 0, self.skill_python.ids)],
        )
        self._task(
            name='Hija', allocated_hours=3.0,
            date_deadline=fields.Datetime.now() + timedelta(days=1),
            required_skill_ids=[(6, 0, self.skill_python.ids)],
            parent_id=parent.id,
        )
        wizard = self._wizard()
        wizard.action_compute()
        # Solo la hija (3.0) cuenta — el padre (999.0) queda excluido por
        # tener child_ids, para no duplicar el esfuerzo.
        self.assertEqual(self._line(wizard, self.skill_python).committed_hours, 3.0)

    def test_available_hours_discounts_existing_assignment(self):
        self._task(
            name='Requiere python', allocated_hours=4.0,
            date_deadline=fields.Datetime.now() + timedelta(days=2),
            required_skill_ids=[(6, 0, self.skill_python.ids)],
        )
        # user_both ya tiene 20h asignadas esta semana en otra tarea —
        # deben descontarse de SU disponibilidad sin importar la skill.
        self._task(
            name='Ya asignada a user_both', allocated_hours=20.0,
            date_deadline=fields.Datetime.now() + timedelta(days=2),
            user_ids=[(6, 0, self.user_both.ids)],
        )
        wizard = self._wizard(horizon_weeks=1)
        wizard.action_compute()
        line = self._line(wizard, self.skill_python)
        # Candidatos con python: user_both (40h calendario - 20h ya
        # asignadas = 20h) + user_python_only (40h calendario, sin nada
        # asignado) = 60h.
        self.assertEqual(line.available_hours, 60.0)

    def test_gap_hours_can_go_negative(self):
        self._task(
            name='Demanda enorme', allocated_hours=1000.0,
            date_deadline=fields.Datetime.now() + timedelta(days=2),
            required_skill_ids=[(6, 0, self.skill_python.ids)],
        )
        wizard = self._wizard(horizon_weeks=1)
        wizard.action_compute()
        line = self._line(wizard, self.skill_python)
        self.assertLess(line.gap_hours, 0.0)

    def test_recompute_clears_previous_lines(self):
        self._task(
            name='Primera corrida', allocated_hours=4.0,
            date_deadline=fields.Datetime.now() + timedelta(days=2),
            required_skill_ids=[(6, 0, self.skill_go.ids)],
        )
        wizard = self._wizard()
        wizard.action_compute()
        self.assertTrue(self._line(wizard, self.skill_go))
        self.assertFalse(self._line(wizard, self.skill_python))

        self._task(
            name='Segunda corrida', allocated_hours=4.0,
            date_deadline=fields.Datetime.now() + timedelta(days=2),
            required_skill_ids=[(6, 0, self.skill_python.ids)],
        )
        wizard.action_compute()
        self.assertEqual(len(wizard.line_ids), 2)

    def test_publish_without_computing_raises(self):
        wizard = self._wizard()
        with self.assertRaises(UserError):
            wizard.action_publish()

    def test_action_publish_creates_knowledge_asset_version(self):
        self._task(
            name='Para publicar', allocated_hours=8.0,
            date_deadline=fields.Datetime.now() + timedelta(days=2),
            required_skill_ids=[(6, 0, self.skill_python.ids)],
        )
        wizard = self._wizard(horizon_weeks=2)
        wizard.action_compute()
        wizard.action_publish()

        asset = self.env['knowledge.asset'].search([
            ('res_model', '=', 'res.company'),
            ('res_id', '=', self.env.company.id),
            ('category', '=', 'project_improve.capacity_report'),
        ])
        self.assertEqual(len(asset), 1)
        payload = asset.current_version_id.payload
        self.assertEqual(payload['horizon_weeks'], 2)
        self.assertEqual(len(payload['items']), 1)
        self.assertEqual(payload['items'][0]['skill'], self.skill_python.name)

        # Publicar de nuevo (otra corrida) agrega una versión, no un asset.
        wizard2 = self._wizard(horizon_weeks=2)
        wizard2.action_compute()
        wizard2.action_publish()
        assets = self.env['knowledge.asset'].search([
            ('res_model', '=', 'res.company'),
            ('res_id', '=', self.env.company.id),
            ('category', '=', 'project_improve.capacity_report'),
        ])
        self.assertEqual(len(assets), 1)
        self.assertEqual(len(assets.version_ids), 2)
