def migrate(cr, version):
    """is_milestone (Boolean plano) se reemplaza por project.milestone
    nativo de Odoo (project.task.milestone_id). Cada tarea marcada como
    hito pasa a ser una tarea real enlazada a un project.milestone nuevo
    (mismo nombre que la tarea), en vez de una tarea sin effort/duration
    forzada a "hito" solo en el export TJP. Corre en pre-migrate porque
    necesita leer is_milestone antes de que el ORM dropee la columna al
    actualizar el módulo con el campo ya removido del modelo.
    """
    cr.execute("""
        SELECT id, name, project_id
        FROM project_task
        WHERE is_milestone IS TRUE AND project_id IS NOT NULL
    """)
    tasks = cr.fetchall()
    if not tasks:
        return

    project_ids = tuple({row[2] for row in tasks})
    cr.execute(
        "UPDATE project_project SET allow_milestones = TRUE WHERE id IN %s",
        (project_ids,),
    )

    for task_id, name, project_id in tasks:
        cr.execute(
            """
            INSERT INTO project_milestone (name, project_id)
            VALUES (%s, %s)
            RETURNING id
            """,
            (name or 'Hito', project_id),
        )
        milestone_id = cr.fetchone()[0]
        cr.execute(
            "UPDATE project_task SET milestone_id = %s WHERE id = %s",
            (milestone_id, task_id),
        )
