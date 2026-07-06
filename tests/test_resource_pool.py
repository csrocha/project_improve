# -*- coding: utf-8 -*-
"""Regression tests for project.task.resource_pool_ids (models/project_task.py).

Covers the skill-based candidate pool: a task with no required skills falls
back to its manual user_ids, a task with required skills only pools
employees who have every one of them, and a project-level candidate roster
(project.project.candidate_user_ids) further restricts that pool.
"""
from odoo.tests.common import TransactionCase


class TestResourcePool(TransactionCase):

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

    def test_no_required_skills_falls_back_to_user_ids(self):
        task = self._task(name='No skills task', user_ids=[(6, 0, [self.user_none.id])])
        self.assertEqual(task.resource_pool_ids, self.user_none)

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
