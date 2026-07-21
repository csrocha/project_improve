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

### ~~1. Campo de prioridad/peso en `project.project`~~ — RESUELTO

Resuelto en v17.0.1.1.3 (2026-07-14): `resource_priority` (Integer,
default 10) agregado como campo "tonto" sin cómputo propio. Ver
CHANGELOG.md [17.0.1.1.3]. Pendiente: `insight_project` todavía no lo
consume (ver su BACKLOG.md ítem 5).

### ~~2. Exponer la prioridad en la UI de staffing~~ — RESUELTO

Resuelto en v17.0.1.1.3 (2026-07-14): agregado a la pestaña "Equipo
asignado". De paso se agregó también el campo `state` (ciclo de vida de
portfolio scheduling) como statusbar en el header, con sus botones de
transición — ver CHANGELOG.md [17.0.1.1.3].

### ~~3. Reporte de capacidad agregada por skill (portfolio)~~ — RESUELTO

Resuelto (2026-07-18): wizard `project.capacity.report.wizard` (Proyectos
→ Reportes → "Capacidad agregada por skill"). Comprometido = `_compute_
resource_pool_ids` como demanda declarada (`required_skill_ids`/
`extra_skill_group_ids`), no asignación real post-TJ3. Disponible =
`resource.calendar.get_work_hours_count` de cada candidato menos lo que
ya tiene asignado (`task.user_ids`). Horizonte configurable en semanas;
nivel de skill tratado binario (no ponderado por `level_progress`);
publicación como `knowledge.asset` queda fuera de esta iteración (paso
posterior, como ya aclaraba este ítem). Detalle completo en
`CHANGELOG.md` [17.0.1.2.0]. 8 tests nuevos en `tests/
test_capacity_report.py`, 18/18 OK.

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
