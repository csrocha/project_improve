# -*- coding: utf-8 -*-
from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

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
    is_milestone = fields.Boolean(
        string='Hito',
        help='Tarea de duración cero que marca un evento significativo '
             '(fin de etapa, documento listo, etc.), pensada para disparar '
             'comunicaciones a usuarios o clientes.',
    )
