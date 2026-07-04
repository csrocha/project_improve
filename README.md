# Project Improve

Tres campos genéricos sobre `project.task`, sin ningún motor de scheduling
detrás — pensados para que otros addons los usen sin arrastrar
[`insight_project`](https://github.com/csrocha/insight_project)
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
