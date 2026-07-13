# BACKLOG

Ideas y mejoras propuestas para `project_improve` que todavía no se
implementaron. Primer archivo de este tipo para este módulo (mismo
formato que `insight_project/BACKLOG.md`): a diferencia del
`CHANGELOG.md` (lo que ya se hizo), acá va lo que falta.

---

## Del backlog de ecosistema (2026-07-13)

Propuesta de "nivel profesional superior" para todo el ecosistema
(`insight_project`, `project_improve`, `insight_project_purchase`,
`work_item_*`, `knowledge_asset`, `odoo_ai_core`). Visión completa en la
memoria `project_ecosystem_roadmap`.

### 1. Campo de prioridad/peso en `project.project`

Agregar `resource_priority` (Selection o Integer) en `project.project`,
campo "tonto" igual que `is_critical_path` — no calcula nada por sí
mismo, es solo el dato que otro módulo (`insight_project`) va a leer para
desempatar conflictos de asignación entre proyectos (ver
`insight_project/BACKLOG.md` ítem 5). Confirmado por auditoría de código
(2026-07-13): hoy no existe ningún campo de prioridad a nivel
`project.project` en este módulo ni en `insight_project` — solo existe
`project.task.priority` (nativo de Odoo, binario Low/High), que es una
cosa completamente distinta.

### 2. Exponer la prioridad en la UI de staffing

Una vez que exista el campo del ítem 1, agregarlo a la pestaña "Equipo
asignado" de `project.project` para que se pueda fijar sin entrar a
developer mode.

### 3. Reporte de capacidad agregada por skill (portfolio)

Hoy `_compute_resource_pool_ids` (`project_task.py`,
`project_task_skill_group.py`) resuelve el pool de candidatos **por
tarea/puesto**, dentro de un solo proyecto — no existe ninguna
agregación a nivel organización de cuánta capacidad por
`hr.skill`/equipo está comprometida entre TODOS los proyectos activos a
la vez. Idea: un reporte (acá o en un módulo de reporting nuevo) que
recorra todos los proyectos en ejecución y sume, por skill,
comprometido vs. disponible — puede reusar `_compute_resource_pool_ids`
como base de cálculo por tarea, agregando por encima. Publicarlo después
como `knowledge.asset` (igual patrón que los reportes de costo de
`insight_project` v17.0.9.7.0) es un paso posterior, no parte de este
ítem.

_Fuente: backlog de ecosistema propuesto por el usuario (2026-07-13,
"Épica 1" ítems 1 y 3, "Épica 3" ítem 1)._
