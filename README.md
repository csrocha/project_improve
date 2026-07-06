# Project Improve

Campos genéricos sobre `project.task`/`project.project`, sin ningún motor
de scheduling detrás — pensados para que otros addons los usen sin
arrastrar [`insight_project`](https://github.com/csrocha/insight_project)
(TaskJuggler) como dependencia:

- **`blocked`** (Boolean, con tracking): impedimento temporal que no
  reemplaza `stage_id` ni `state`, puede coexistir con cualquier
  etapa/estado activo. No almacena el motivo (queda en el chatter o en
  donde cada addon consumidor decida registrarlo).
- **`is_critical_path`** (Boolean): campo plano, sin `compute`. Sin
  `insight_project` instalado queda en `False` (o se puede setear a mano);
  con `insight_project` instalado, ese addon le agrega el `compute` que lo
  deriva del schedule de TaskJuggler.
- **`is_milestone`** (Boolean, "Hito"): tarea de duración cero que marca un
  evento significativo — pensado para disparar comunicaciones/actividades
  a usuarios o clientes ("etapa terminada", "documento listo") desde
  addons que todavía no existen, sin que necesiten TaskJuggler para nada.
- **`required_skill_ids`** (Many2many `hr.skill`, en `project.task`):
  skills necesarias para hacer la tarea, reutilizando el módulo estándar
  `hr_skills` de Odoo.
- **`resource_pool_ids`** (Many2many `res.users`, en `project.task`,
  computado y editable): pool de candidatos a hacer la tarea. Sin
  `required_skill_ids` cae a `user_ids`; con skills requeridas, se arma
  con los empleados que las tengan **todas**, filtrado además por
  `project.candidate_user_ids` si esa lista no está vacía. Al ser
  `store=True, readonly=False`, se puede ajustar a mano — el ajuste
  persiste hasta el próximo cambio de `required_skill_ids` o de
  `candidate_user_ids`.
- **`candidate_user_ids`** (Many2many `res.users`, en `project.project`):
  roster de empleados considerados para la asignación automática de tareas
  de ese proyecto. Vacío = considerar a todos los empleados de la
  compañía.

`insight_project` consume `resource_pool_ids` para armar el `allocate` que
le manda a TaskJuggler (con `alternative`/`select`, para que TJ3 elija de
verdad entre los candidatos), pero el pool en sí es staffing genérico —
útil aunque no se use TaskJuggler.

## Consumidores conocidos

- [`insight_project`](https://github.com/csrocha/insight_project): agrega
  el `compute` de `is_critical_path` vía su motor CPM.
- [`work_item_task`](https://github.com/csrocha/work_item_task): decora el
  work item con ⚡ (`is_critical_path`) y aplica `blocked = True` al cerrar
  un período si la plantilla de cierre lo indica; excluye hitos de "mis
  tareas de la semana".

Ninguno de los dos depende del otro — ambos cuelgan de este addon.

## License

OPL-1 — Cristian S. Rocha <csrocha@gmail.com>
