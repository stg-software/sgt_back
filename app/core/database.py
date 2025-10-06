# app/core/database.py
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL no está configurado en .env")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ============================================================================
# FUNCIÓN PARA SEED AUTOMÁTICO
# ============================================================================
def seed_initial_data():
    """Poblar datos iniciales si no existen"""
    from app.models.roles import Role
    from app.models.workflow import WorkflowTemplate, WorkflowState
    from app.models.user import User
    from app.core.security import hash_password
    
    db = SessionLocal()
    
    try:
        # ========== SEED DE ROLES ==========
        roles_data = [
            {"name": "Administrador", "description": "Acceso completo al sistema"},
            {"name": "Manager", "description": "Gestión de equipos y tareas"},
            {"name": "Supervisor", "description": "Supervisión de tareas"},
            {"name": "Agente", "description": "Ejecución de tareas"},
            {"name": "Visualizador", "description": "Solo lectura"},
        ]
        
        for role_data in roles_data:
            exists = db.query(Role).filter_by(name=role_data["name"]).first()
            if not exists:
                db.add(Role(name=role_data["name"], description=role_data["description"]))
                print(f"✅ Rol creado: {role_data['name']}")
        
        db.commit()
        
        # ========== SEED DE WORKFLOWS ==========
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
        
        for wf in workflows_data:
            exists = db.query(WorkflowTemplate).filter_by(name=wf["name"]).first()
            if not exists:
                workflow = WorkflowTemplate(name=wf["name"])
                db.add(workflow)
                db.commit()
                db.refresh(workflow)
                
                for i, state in enumerate(wf["states"], start=1):
                    db.add(WorkflowState(name=state, order=i, workflow_id=workflow.id))
                
                print(f"✅ Workflow creado: {wf['name']}")
        
        db.commit()
        
        # ========== SEED DE USUARIO ADMIN ==========
        admin_exists = db.query(User).filter_by(username="admin").first()
        if not admin_exists:
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
                print("✅ Usuario admin creado (username=admin, password=admin123)")
            else:
                print("⚠️ No se pudo crear usuario admin: rol 'Administrador' no encontrado")
        
        print("\n🎉 Seed inicial completado exitosamente\n")
        
    except Exception as e:
        print(f"❌ Error en seed inicial: {e}")
        db.rollback()
    finally:
        db.close()


# ============================================================================
# EVENTO: Ejecutar seed después de crear tablas
# ============================================================================
@event.listens_for(Base.metadata, 'after_create')
def receive_after_create(target, connection, **kw):
    """
    Este evento se ejecuta automáticamente después de crear las tablas.
    Solo se activa cuando usas Base.metadata.create_all()
    """
    print("\n📦 Tablas creadas. Ejecutando seed inicial...")
    seed_initial_data()