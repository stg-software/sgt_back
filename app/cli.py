# app/cli.py
import click
from app.core.database import SessionLocal, Base, engine
from app.models.roles import Role
from app.models.workflow import WorkflowTemplate, WorkflowState
from app.models.user import User
from app.core.security import hash_password


@click.group()
def cli():
    """SGT_v1 - Comandos de gestión"""
    pass


@cli.command()
def init_db():
    """Crear tablas y poblar datos iniciales"""
    click.echo("📦 Creando tablas...")
    Base.metadata.create_all(bind=engine)
    click.echo("✅ Tablas creadas")
    
    click.echo("\n📦 Poblando datos iniciales...")
    seed_data()
    click.echo("✅ Datos iniciales creados\n")


@cli.command()
def seed():
    """Poblar datos iniciales (sin crear tablas)"""
    click.echo("📦 Poblando datos iniciales...")
    seed_data()
    click.echo("✅ Datos iniciales creados\n")


@cli.command()
def reset_db():
    """PELIGRO: Eliminar y recrear todas las tablas"""
    if click.confirm('⚠️  ¿Estás seguro? Esto eliminará TODOS los datos'):
        click.echo("🗑️  Eliminando tablas...")
        Base.metadata.drop_all(bind=engine)
        click.echo("📦 Recreando tablas...")
        Base.metadata.create_all(bind=engine)
        click.echo("📦 Poblando datos iniciales...")
        seed_data()
        click.echo("✅ Base de datos reseteada\n")


def seed_data():
    """Función auxiliar para poblar datos"""
    db = SessionLocal()
    
    try:
        # ROLES
        roles_data = [
            {"name": "Administrador", "description": "Acceso completo al sistema"},
            {"name": "Manager", "description": "Gestión de equipos y tareas"},
            {"name": "Supervisor", "description": "Supervisión de tareas"},
            {"name": "Agente", "description": "Ejecución de tareas"},
            {"name": "Visualizador", "description": "Solo lectura"},
        ]
        
        for role_data in roles_data:
            if not db.query(Role).filter_by(name=role_data["name"]).first():
                db.add(Role(**role_data))
                click.echo(f"  ✓ Rol: {role_data['name']}")
        db.commit()
        
        # WORKFLOWS
        workflows_data = [
            {"name": "Scrum", "states": ["To Do", "In Progress", "In Review", "Done"]},
            {"name": "Kanban Básico", "states": ["Pendiente", "En Proceso", "Completado"]},
            {"name": "Soporte IT", "states": ["Nuevo", "Asignado", "En Progreso", "Resuelto", "Cerrado"]},
            {"name": "Marketing", "states": ["Idea", "Planificación", "Ejecución", "Finalizado"]},
            {"name": "Ventas", "states": ["Prospecto", "En Negociación", "Cerrado Exitoso", "Cerrado Perdido"]},
            {"name": "Reclutamiento", "states": ["Vacante Abierta", "Entrevista", "Oferta", "Contratado", "Rechazado"]},
            {"name": "Proyecto", "states": ["Inicio", "Planificación", "Ejecución", "Monitoreo", "Cierre"]},
            {"name": "Mantenimiento", "states": ["Programado", "En Ejecución", "Finalizado"]},
            {"name": "Producción", "states": ["En Cola", "En Proceso", "Control Calidad", "Completado"]},
            {"name": "Custom Simple", "states": ["Pendiente", "Hecho"]}
        ]
        
        for wf_data in workflows_data:
            if not db.query(WorkflowTemplate).filter_by(name=wf_data["name"]).first():
                workflow = WorkflowTemplate(name=wf_data["name"])
                db.add(workflow)
                db.commit()
                db.refresh(workflow)
                
                for i, state_name in enumerate(wf_data["states"], start=1):
                    db.add(WorkflowState(name=state_name, order=i, workflow_id=workflow.id))
                
                click.echo(f"  ✓ Workflow: {wf_data['name']}")
        db.commit()
        
        # USUARIO ADMIN
        if not db.query(User).filter_by(username="admin").first():
            admin_role = db.query(Role).filter_by(name="Administrador").first()
            if admin_role:
                admin = User(
                    username="admin",
                    first_name="Super",
                    last_name="Admin",
                    email="admin@example.com",
                    password=hash_password("admin123"),
                    role_id=admin_role.id,
                )
                db.add(admin)
                db.commit()
                click.echo("  ✓ Usuario admin creado")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == '__main__':
    cli()