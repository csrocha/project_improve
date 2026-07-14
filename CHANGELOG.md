# CHANGELOG

Formato basado en [Keep a Changelog](https://keepachangelog.com/es/1.1.0/).
Versionado: `17.0.MAYOR.MENOR.PARCHE`.

Cada entrada de version incluye el **prompt** que motivo los cambios
y las **discusiones de diseno** relevantes que influyeron en las decisiones,
para trazabilidad completa del razonamiento de agentes de IA.

---

## [17.0.1.1.3] - 2026-07-14

### Prompt

> "Dentro del backlog hay una funcionalidad que quiero darle más
> prioridad, que corresponde a los estados de los proyectos en draft,
> evaluación y en progreso. Estamos listos para implementarla?" / "La
> implementación de ORM debe ser contra project_improve, ahí debe estar
> el campo estado y el orden de prioridad entre proyectos." / "Acomodemos
> la UI. Es estado de planificación tiene que estar en el head del
> formulario con un widget de estado. Hay que agregar los botones para
> pasar de estado: Draft - [Evaluate] -> Evaluating / Evaluating -
> [Start] -> On Process / Evaluating - [Discard] -> Draft / On Process -
> [Finish] -> Finished / On Process - [Reavaluate] -> Evaluating."

### Discusión de diseño

- Los campos nuevos (`state`, `resource_priority`) van en `project_improve`
  y no en `insight_project` porque este último ya depende de aquel
  (confirmado contra el manifest) — mismo lugar que `candidate_user_ids`,
  el único otro campo que este módulo agrega a `project.project`. El
  motor de scheduling multi-proyecto que consume estos campos queda en
  `insight_project` (ver su CHANGELOG).
- `resource_priority`: el backlog dejaba abierto si debía ser Selection o
  Integer — se decidió Integer libre (escala abierta para desempatar
  entre muchos proyectos), aunque todavía no tiene consumidor (queda
  pendiente en `insight_project/BACKLOG.md` ítem 5).
- Se descartó agregar un botón "Reabrir" desde el estado Finalizado — el
  usuario prefirió dejarlo como callejón terminal y en cambio abrir la
  idea de "Clonar proyecto" con calibración histórica de esfuerzo (ver
  memoria `project_clone_template_design` / `insight_project/BACKLOG.md`
  ítem 8), sin implementar todavía.

### Agregado

- `project.project.state` (Selection: draft/evaluation/progress/done,
  default draft, `tracking=True`) — ciclo de vida de planificación de
  portfolio, distinto de `stage_id`/Kanban de tareas.
- `project.project.resource_priority` (Integer, default 10) — campo
  "tonto" sin cómputo propio, mismo espíritu que `is_critical_path`.
- Botones de transición de estado (`action_evaluate`, `action_start`,
  `action_discard`, `action_finish`, `action_reevaluate`) y widget
  statusbar en el header del form de Proyecto.

### Cambiado

- `views/project_project_views.xml`: `resource_priority` se agregó a la
  pestaña "Equipo asignado"; `state` se muestra como statusbar en el
  header (no en una pestaña), junto a los botones de transición.

### Validación

- Suite completa de `insight_project` (que consume estos campos) en
  verde tras el cambio: `make test-local MODULE=insight_project`,
  199/199 tests, 0 fallos.

---

## [17.0.1.1.2] - 2026-07-10

### Prompt

> "Sigamos con el backlog de TJ3" → ítem "allocate con múltiples roles
> obligatorios por tarea" → el usuario rechazó la idea de "roles" con
> nombre fijo: "No quiero poner roles aquí, solo skills [...] Los roles
> surgen a partir de las oportunidades. Es lo mismo que en el primer
> partido de fútbol con tus amigos [...] deciden dónde va cada uno para
> armar un equipo lo más completo posible." → sobre dónde vivir el
> modelo: "En project_improve".

### Discusión de diseño

- El punto de partida fue un pedido de TJ3 (soportar `allocate` con
  varios recursos obligatorios simultáneos por tarea, ver
  `insight_project`), pero el usuario pivoteó el diseño: en vez de un
  modelo de "roles" con nombre fijo (Dev/Reviewer), quiso generalizar el
  mecanismo de skills que ya existía (`project.task.required_skill_ids`
  → `resource_pool_ids` calculado) a "N puestos simultáneos", cada uno
  con su propio filtro de skills — sin etiqueta de rol.
- Por eso el modelo nuevo vive acá (`project_improve`), no en
  `insight_project`: es donde ya está el mecanismo de matching por
  skills, y este es su generalización natural (de 1 puesto por tarea a
  N puestos simultáneos), no algo específico de TaskJuggler.
  `insight_project` solo lo consume (lee `extra_skill_group_ids`) para
  decidir cómo emitir el `allocate`.
- `project.task.skill.group`: mismo patrón que el puesto principal de la
  tarea (`required_skill_ids` Many2many + `resource_pool_ids` Many2many
  computado/ajustable a mano), pero exige `required_skill_ids` no vacío
  (constrains): si no hace falta filtrar por skill, no hace falta un
  grupo aparte — el pool de la tarea ya cubre ese puesto.

### Agregado

- Modelo `project.task.skill.group` (`models/project_task_skill_group.py`):
  `task_id`, `required_skill_ids`, `resource_pool_ids` (compute igual al
  de `project.task`, scoped al grupo).
- `project.task.extra_skill_group_ids` (One2many): puestos adicionales de
  una tarea, cubiertos en simultáneo con su pool principal.
- Vista: lista embebida en la pestaña "Staffing" del form de Tarea.
- `security/ir.model.access.csv` (el módulo no tenía ninguno hasta ahora,
  porque solo extendía modelos existentes).
- Tests en `tests/test_resource_pool.py` (`TestTaskSkillGroup`): matching
  por skill del grupo, constraint de skills vacías, restricción por
  `candidate_user_ids` del proyecto, independencia entre grupos de la
  misma tarea.

---

## [17.0.1.1.1] - 2026-07-07

### Prompt

> "En la vista de Form de Proyecto aparece todas las propiedades de
> insight_project y project_improve. Deberíamos separar las cosas: Lo de
> project_improve debería ir en Settings, y mejor si acomodamos con
> temática en las secciones TASK MANAGEMENT y TIME MANAGEMENT."
>
> Sobre `candidate_user_ids`: "se merece su propia hoja. Esa hoja sería
> 'Candidatos' o 'Recursos' o 'Equipo de asignado'."
>
> Sobre los skills de tarea: "Falta que aparezcan los skills requeridos
> en la vista de tareas. Habría que agregarlos en una página dentro del
> formulario. Los skills pertenecen a project_improve."

### Discusión de diseño

- `project_improve` no tenía ninguna vista propia (`'data': []` en el
  manifest) — `candidate_user_ids` (Proyecto) y
  `required_skill_ids`/`resource_pool_ids` (Tarea) los exponía
  `insight_project`, mezclados con su configuración de TaskJuggler y, en
  el caso de `candidate_user_ids`, escondidos detrás de
  `invisible="not is_tj_enabled"` aunque `_compute_resource_pool_ids` los
  use independientemente de si TaskJuggler está instalado o habilitado.
- Se evaluó acomodarlos en Settings > Task Management / Time Management
  del form nativo de `project.edit_project`, pero se descartó: son datos
  de trabajo diario (a quién se puede asignar una tarea), no ajustes de
  un toggle — mejor pestañas propias, separadas de `insight_project`.

### Agregado

- `views/project_project_views.xml`: pestaña "Equipo asignado" en el
  form de Proyecto con `candidate_user_ids`, sin el gating de
  `is_tj_enabled` que lo escondía antes.
- `views/project_task_views.xml`: pestaña "Staffing" en el form de Tarea
  con `required_skill_ids`/`resource_pool_ids`.

---

## [17.0.1.1.0] - 2026-07-07

### Prompt

> "Veo que algo hicimos mal en la importación y exportación de tjp,
> específicamente en el tema milestone. Estamos agregando milestone en el
> proyecto como tasks, pero son tasks? Por favor revisa una mejor
> implementación de la que estamos teniendo ahora sin usar el
> is_milestone, sino usando las características propias del addon
> project."

### Discusión de diseño

- `is_milestone` era un boolean plano sin ningún modelo propio detrás.
  Odoo ya trae `project.milestone` en el addon `project` community (no
  hace falta Enterprise): un registro a nivel proyecto con `name`,
  `deadline`, `is_reached`, `reached_date` y `task_ids` (inverso de
  `project.task.milestone_id`), con vista, grupo de seguridad
  (`group_project_milestone`) y tracking de chatter propios — exactamente
  "las características propias del addon project" que pedía el prompt.
- Se decidió mover el hito de "propiedad de una tarea" a "objeto de
  proyecto enlazado a tareas" en vez de solo cambiar el nombre del campo,
  porque TaskJuggler y Odoo entienden "milestone" de forma distinta: TJ3
  lo trata como una tarea puntual de 0 esfuerzo; Odoo lo trata como un
  hito al que *varias* tareas reales pueden apuntar. Mantener el hack de
  "esta tarea real, edítenle is_milestone y pierde su effort/duration" no
  se resuelve renombrando el campo — la lógica de export en
  `insight_project` pasa a generar una tarea TJP sintética por cada
  `project.milestone`, separada de las tareas reales (ver CHANGELOG de
  `insight_project`).
- Migración de datos en `migrations/17.0.1.1.0/pre-migrate.py`: por cada
  tarea con `is_milestone=True`, crea un `project.milestone` (mismo
  nombre) y la enlaza vía `milestone_id`, además de forzar
  `allow_milestones=True` en los proyectos afectados. Corre en
  pre-migrate porque necesita leer la columna antes de que el ORM la
  dropee al detectar que el campo ya no existe en el modelo.

### Quitado

- `project.task.is_milestone` (Boolean). Ver `project.task.milestone_id`
  (nativo de `project`) como reemplazo.

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
