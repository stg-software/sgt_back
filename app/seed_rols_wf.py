from sqlalchemy.orm import Session
from app.core.database import SessionLocal, Base, engine
from app import models  # asegura que todo se registre
from app.models.roles import Role
from app.models.workflow import WorkflowTemplate, WorkflowState


# Datos por defecto
roles_data = [
    {"name": "Administrador", "description": "Acceso completo al sistema"},
    {"name": "Manager", "description": "Gestión de equipos y tareas"},
    {"name": "Supervisor", "description": "Supervisión de tareas"},
    {"name": "Agente", "description": "Ejecución de tareas"},
    {"name": "Visualizador", "description": "Solo lectura"},
]

workflows_data = [
    {
        "name": "Scrum",
        "states": ["To Do", "In Progress", "In Review", "Done"]
    },
    {
        "name": "Kanban Básico",
        "states": ["Pendiente", "En Proceso", "Completado"]
    },
    {
        "name": "Soporte IT",
        "states": ["Nuevo", "Asignado", "En Progreso", "Resuelto", "Cerrado"]
    },
    {
        "name": "Marketing",
        "states": ["Idea", "Planificación", "Ejecución", "Finalizado"]
    },
    {
        "name": "Ventas",
        "states": ["Prospecto", "En Negociación", "Cerrado Exitoso", "Cerrado Perdido"]
    },
    {
        "name": "Reclutamiento",
        "states": ["Vacante Abierta", "Entrevista", "Oferta", "Contratado", "Rechazado"]
    },
    {
        "name": "Proyecto",
        "states": ["Inicio", "Planificación", "Ejecución", "Monitoreo", "Cierre"]
    },
    {
        "name": "Mantenimiento",
        "states": ["Programado", "En Ejecución", "Finalizado"]
    },
    {
        "name": "Producción",
        "states": ["En Cola", "En Proceso", "Control Calidad", "Completado"]
    },
    {
        "name": "Custom Simple",
        "states": ["Pendiente", "Hecho"]
    }
]


def seed():
    Base.metadata.create_all(bind=engine)  # asegura que las tablas existen
    db: Session = SessionLocal()

    # Insertar roles
    for role in roles_data:
        exists = db.query(Role).filter_by(name=role["name"]).first()
        if not exists:
            db.add(Role(name=role["name"], description=role["description"]))
    db.commit()

    # Insertar workflows
    for wf in workflows_data:
        exists = db.query(WorkflowTemplate).filter_by(name=wf["name"]).first()
        if not exists:
            workflow = WorkflowTemplate(name=wf["name"])
            db.add(workflow)
            db.commit()
            db.refresh(workflow)

            for i, state in enumerate(wf["states"], start=1):
                db.add(WorkflowState(name=state, order=i, workflow_id=workflow.id))
    db.commit()

    db.close()
    print("✅ Seed completado: roles y workflows iniciales creados.")


if __name__ == "__main__":
    seed()
