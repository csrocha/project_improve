# -*- coding: utf-8 -*-
"""Regression tests for project.task.resource_pool_ids (models/project_task.py).

Covers the skill-based candidate pool: a task with no required skills falls
back to its manual user_ids, a task with required skills only pools
employees who have every one of them, and a project-level candidate roster
(project.project.candidate_user_ids) further restricts that pool.
"""
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class SkillPoolFixtures:
    """Fixtures compartidas por TestResourcePool y TestTaskSkillGroup — sin
    métodos test_*, para no re-ejecutar los tests de una clase dentro de la
    otra por herencia."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.project = cls.env['project.project'].create({'name': 'Pool Project'})

        cls.skill_type = cls.env['hr.skill.type'].create({
            'name': 'Programming Test',
            'skill_level_ids': [
                (0, 0, {'name': 'Beginner', 'level_progress': 25}),
                (0, 0, {'name': 'Expert', 'level_progress': 100, 'default_level': True}),
            ],
        })
        cls.skill_level = cls.skill_type.skill_level_ids.filtered('default_level')
        cls.skill_python, cls.skill_go = cls.env['hr.skill'].create([
            {'name': 'Python', 'skill_type_id': cls.skill_type.id},
            {'name': 'Go', 'skill_type_id': cls.skill_type.id},
        ])

        cls.user_both = cls._make_employee_user('Both', cls.skill_python | cls.skill_go)
        cls.user_python_only = cls._make_employee_user('PyOnly', cls.skill_python)
        cls.user_none = cls._make_employee_user('NoSkill', cls.env['hr.skill'])

    @classmethod
    def _make_employee_user(cls, name, skills):
        user = cls.env['res.users'].with_context(no_reset_password=True).create({
            'name': name,
            'login': f'{name.lower()}@pool.test',
            'email': f'{name.lower()}@pool.test',
            'groups_id': [(4, cls.env.ref('base.group_user').id)],
        })
        employee = cls.env['hr.employee'].create({'name': name, 'user_id': user.id})
        for skill in skills:
            cls.env['hr.employee.skill'].create({
                'employee_id': employee.id,
                'skill_id': skill.id,
                'skill_type_id': skill.skill_type_id.id,
                'skill_level_id': cls.skill_level.id,
            })
        return user

    def _task(self, **vals):
        vals.setdefault('project_id', self.project.id)
        return self.env['project.task'].create(vals)


class TestResourcePool(SkillPoolFixtures, TransactionCase):

    def test_no_required_skills_falls_back_to_user_ids(self):
        task = self._task(name='No skills task', user_ids=[(6, 0, [self.user_none.id])])
        self.assertEqual(task.resource_pool_ids, self.user_none)

    def test_reassigning_user_ids_without_skills_updates_pool(self):
        """Bug real de producción (2026-08-26, proyecto 'Autodiagnóstico y
        Sistema de Oportunidades ProPyMES'): resource_pool_ids no dependía
        de user_ids, así que reasignar una tarea sin required_skill_ids
        (cambiar el "Asignado a" de un usuario a otro) dejaba el pool de
        candidatos de TJ3 pegado al asignado ORIGINAL -- TJ3 seguía
        programando a quien ya no era responsable de la tarea, en vez de
        a quien Odoo mostraba como asignado."""
        task = self._task(name='Reasignada', user_ids=[(6, 0, [self.user_none.id])])
        self.assertEqual(task.resource_pool_ids, self.user_none)

        task.user_ids = [(6, 0, [self.user_both.id])]
        self.assertEqual(task.resource_pool_ids, self.user_both)

    def test_pool_matches_employees_with_all_required_skills(self):
        task = self._task(
            name='Needs python+go',
            required_skill_ids=[(6, 0, (self.skill_python | self.skill_go).ids)],
        )
        self.assertEqual(task.resource_pool_ids, self.user_both)

    def test_pool_excludes_employees_missing_a_skill(self):
        task = self._task(
            name='Needs python only',
            required_skill_ids=[(6, 0, self.skill_python.ids)],
        )
        self.assertEqual(task.resource_pool_ids, self.user_both | self.user_python_only)

    def test_empty_project_candidate_list_means_everyone(self):
        self.assertFalse(self.project.candidate_user_ids)
        task = self._task(
            name='Needs python unrestricted',
            required_skill_ids=[(6, 0, self.skill_python.ids)],
        )
        self.assertEqual(task.resource_pool_ids, self.user_both | self.user_python_only)

    def test_project_candidate_list_restricts_pool(self):
        self.project.candidate_user_ids = [(6, 0, self.user_python_only.ids)]
        task = self._task(
            name='Needs python restricted',
            required_skill_ids=[(6, 0, self.skill_python.ids)],
        )
        self.assertEqual(task.resource_pool_ids, self.user_python_only)
        self.project.candidate_user_ids = [(5, 0, 0)]

    def test_manual_override_persists_until_skills_change(self):
        task = self._task(
            name='Manual override',
            required_skill_ids=[(6, 0, self.skill_python.ids)],
        )
        task.resource_pool_ids = [(6, 0, [self.user_none.id])]
        self.assertEqual(task.resource_pool_ids, self.user_none)

        task.write({'name': 'Manual override renamed'})
        self.assertEqual(task.resource_pool_ids, self.user_none,
                          'un-related write must not recompute the pool')

        task.required_skill_ids = [(6, 0, (self.skill_python | self.skill_go).ids)]
        self.assertEqual(task.resource_pool_ids, self.user_both,
                          'changing required_skill_ids must recompute the pool')


class TestTaskSkillGroup(SkillPoolFixtures, TransactionCase):
    """extra_skill_group_ids: puestos adicionales cubiertos EN SIMULTÁNEO con
    el pool principal de la tarea, cada uno con su propio filtro de skills
    (reusa los mismos fixtures de usuarios/skills que TestResourcePool)."""

    def test_group_pool_matches_its_own_required_skills(self):
        task = self._task(name='Con puesto adicional')
        group = self.env['project.task.skill.group'].create({
            'task_id': task.id,
            'required_skill_ids': [(6, 0, self.skill_go.ids)],
        })
        self.assertEqual(group.resource_pool_ids, self.user_both)

    def test_group_without_skills_raises(self):
        task = self._task(name='Puesto sin skill')
        with self.assertRaises(ValidationError):
            self.env['project.task.skill.group'].create({
                'task_id': task.id,
                'required_skill_ids': [(6, 0, [])],
            })

    def test_group_restricted_by_project_candidates(self):
        self.project.candidate_user_ids = [(6, 0, self.user_both.ids)]
        task = self._task(name='Puesto restringido')
        group = self.env['project.task.skill.group'].create({
            'task_id': task.id,
            'required_skill_ids': [(6, 0, self.skill_python.ids)],
        })
        self.assertEqual(group.resource_pool_ids, self.user_both)
        self.project.candidate_user_ids = [(5, 0, 0)]

    def test_multiple_groups_are_independent(self):
        task = self._task(name='Dos puestos')
        group_python = self.env['project.task.skill.group'].create({
            'task_id': task.id,
            'required_skill_ids': [(6, 0, self.skill_python.ids)],
        })
        group_go = self.env['project.task.skill.group'].create({
            'task_id': task.id,
            'required_skill_ids': [(6, 0, self.skill_go.ids)],
        })
        self.assertEqual(group_python.resource_pool_ids, self.user_both | self.user_python_only)
        self.assertEqual(group_go.resource_pool_ids, self.user_both)
        self.assertEqual(task.extra_skill_group_ids, group_python | group_go)
