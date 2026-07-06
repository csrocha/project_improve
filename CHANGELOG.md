# CHANGELOG

Formato basado en [Keep a Changelog](https://keepachangelog.com/es/1.1.0/).
Versionado: `17.0.MAYOR.MENOR.PARCHE`.

Cada entrada de version incluye el **prompt** que motivo los cambios
y las **discusiones de diseno** relevantes que influyeron en las decisiones,
para trazabilidad completa del razonamiento de agentes de IA.

---

## [17.0.1.0.1] - 2026-07-06

### Prompt

> "Estoy viendo un comportamiento no deseado de insight_project. [...] Lo
> que tiene que ocurrir es que deberían tener una lista de personas
> disponibles para atender esas tareas y usar esa lista para enviar al
> taskjuggler. [...] para armar los equipos de trabajo necesitaríamos
> asignarle skills a las tareas. A partir de esas skills seleccionaría a
> las empleados correctos [...] usar skills de Odoo."
>
> Sobre la lista de candidatos por proyecto: "El pool de candidatos puede
> estar restringido usando una lista de candidatos en el proyecto. Si esa
> lista esta vacía hay que usar a todos los empleados."
>
> Sobre dónde debía vivir esta lógica: "Deberíamos pasar todo lo de skills
> que no es propio de tj3 en project_improve."

### Discusión de diseño

- El pool de candidatos por skills y la restricción por roster de proyecto
  no son un concepto de TaskJuggler — son staffing genérico, útil incluso
  sin `insight_project` instalado (p. ej. para sugerir asignación manual) —
  por eso viven acá y no en `insight_project`, que solo los consume al
  generar el `.tjp`.
- Se reutiliza el módulo estándar `hr_skills` de Odoo (`hr.skill`,
  `hr.employee.skill`) en vez de un modelo propio: ya estaba presente en
  el árbol de addons pero sin usar por ningún módulo custom.
  `hr.employee` ya trae un `skill_ids` (Many2many `hr.skill`, computado y
  guardado) a partir de `employee_skill_ids` — se reutiliza tal cual para
  el matching, sin tocar `hr.employee.skill` directamente.
- `resource_pool_ids` es un compute con `store=True, readonly=False`
  (patrón "default computado pero editable" de Odoo): se recalcula
  cuando cambian `required_skill_ids` o `project_id.candidate_user_ids`,
  pero un ajuste manual entre medio se preserva.
- Un empleado necesita **todas** las skills requeridas para entrar al
  pool (no alguna) — se compara por conjunto de ids
  (`required_ids <= set(employee.skill_ids.ids)`), no solo intersección.
- Gotcha de testing: crear `hr.employee.skill` sin pasar `skill_level_id`
  explícito puede violar el `NOT NULL` de esa columna en el insert masivo
  — el compute de `skill_level_id` no llega a tiempo para el `INSERT`
  aunque el campo tenga default declarado. Hay que pasarlo siempre a
  mano al crear estos registros por código.
- Suite corrida contra Odoo real en el contenedor Docker del proyecto
  (`odoo-test`, DB `fop`) — 6 tests, todos en verde.

### Agregado

- `project.task.required_skill_ids` (Many2many `hr.skill`).
- `project.task.resource_pool_ids` (Many2many `res.users`, computado y
  editable — ver discusión de diseño).
- `project.project.candidate_user_ids` (Many2many `res.users`).
- Dependencia a `hr_skills`.
- `tests/test_resource_pool.py`: matching por skills, restricción por
  `candidate_user_ids`, fallback a `user_ids` sin skills requeridas, y
  persistencia de la edición manual del pool.

---

## [17.0.1.0.0]

Scaffold inicial: `blocked`, `is_critical_path`, `is_milestone` sobre
`project.task`.
