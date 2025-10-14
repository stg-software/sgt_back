# app/api/tasks.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, attributes
from typing import List, Dict, Any
from datetime import datetime
from app.core.database import SessionLocal
from app.models.task import Task
from app.models.board import Board
from app.schemas.task import TaskCreate, TaskUpdate, TaskOut, TaskRecordAdd
from app.api.auth import get_current_user
from app.models.user import User
from app.core.permissions import PermissionChecker

router = APIRouter(prefix="/tasks", tags=["Tasks"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def add_record_entry(task: Task, user: User, state_name: str, doc: str):
    """
    Agregar una entrada al historial de la tarea
    
    Args:
        task: Tarea a la que agregar el registro
        user: Usuario que realiza la acción
        state_name: Nombre del estado actual de la tarea
        doc: Comentario/documentación
    """
    now = datetime.now()
    
    new_entry = {
        "fecha": now.strftime("%d/%m/%Y"),
        "hora": now.strftime("%H:%M:%S"),
        "user": user.username,
        "status": state_name,
        "doc": doc
    }
    
    # Asegurar que record sea una lista mutable
    if task.record is None:
        task.record = []
    elif not isinstance(task.record, list):
        task.record = []
    
    # Crear una nueva lista para que SQLAlchemy detecte el cambio
    current_record = list(task.record) if task.record else []
    current_record.append(new_entry)
    task.record = current_record
    
    # Marcar explícitamente el campo como modificado
    attributes.flag_modified(task, "record")

@router.get("", response_model=List[TaskOut])
def list_tasks(
    board_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Listar tareas accesibles para el usuario según su rol"""
    # Obtener tableros accesibles
    accessible_boards = PermissionChecker.get_user_boards(current_user, db)
    accessible_board_ids = [b.id for b in accessible_boards]
    
    # Consulta base: tareas en tableros accesibles
    q = db.query(Task).filter(Task.board_id.in_(accessible_board_ids))
    
    if board_id:
        q = q.filter(Task.board_id == board_id)
    
    role_name = current_user.role.name if current_user.role else None
    
    print(f"\n{'='*80}")
    print(f"🔍 LIST TASKS - Usuario: {current_user.username} ({role_name})")
    
    # Agente: SOLO tareas asignadas a él
    if role_name == "Agente":
        q = q.filter(Task.assigned_to_id == current_user.id)
        tasks = q.all()
        print(f"✅ Agente: filtrando solo {len(tasks)} tareas asignadas")
        print(f"{'='*80}\n")
    
    # Administrador, Manager, Supervisor, Visualizador: todas las tareas
    elif role_name in ["Administrador", "Manager", "Supervisor", "Visualizador"]:
        tasks = q.all()
        print(f"✅ {role_name}: ve {len(tasks)} tareas")
        print(f"{'='*80}\n")
    else:
        tasks = []
        print(f"⚠️ Sin rol válido")
        print(f"{'='*80}\n")
    
    return [TaskOut.model_validate(t) for t in tasks]

@router.put("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Actualizar una tarea según permisos del usuario"""
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    # Verificar si puede editar la tarea
    if not PermissionChecker.can_edit_task(current_user, task, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para editar esta tarea"
        )
    
    # Obtener campos editables según el rol
    editable_fields = PermissionChecker.get_editable_task_fields(current_user, task)
    
    # Aplicar actualizaciones solo a campos permitidos
    update_data = data.model_dump(exclude_unset=True)
    
    # Detectar cambios para agregar al historial
    state_changed = False
    old_state_name = task.state.name if task.state else "Sin estado"
    new_state_name = old_state_name
    
    for field, value in update_data.items():
        if field in editable_fields:
            # Detectar cambio de estado
            if field == "state_id" and value != task.state_id:
                state_changed = True
                from app.models.workflow import WorkflowState
                new_state = db.query(WorkflowState).filter(WorkflowState.id == value).first()
                new_state_name = new_state.name if new_state else "Sin estado"
            
            setattr(task, field, value)
        elif field not in editable_fields and value is not None:
            # Si intenta editar un campo no permitido
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No tienes permisos para editar el campo '{field}'"
            )
    
    # Agregar entrada al historial si cambió el estado
    if state_changed:
        doc = f"Cambió el estado de '{old_state_name}' a '{new_state_name}'"
        add_record_entry(task, current_user, new_state_name, doc)
    
    db.commit()
    db.refresh(task)
    
    return TaskOut.model_validate(task)

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Eliminar una tarea (solo Admin, Manager, Supervisor o creador)"""
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    role_name = current_user.role.name if current_user.role else None
    
    # Admin puede eliminar cualquier tarea
    if role_name == "Administrador":
        db.delete(task)
        db.commit()
        return
    
    # Manager y Supervisor pueden eliminar tareas en sus tableros
    if role_name in ["Manager", "Supervisor"]:
        if PermissionChecker.can_edit_task(current_user, task, db):
            db.delete(task)
            db.commit()
            return
    
    # Creador puede eliminar su propia tarea
    if task.created_by_id == current_user.id:
        db.delete(task)
        db.commit()
        return
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="No tienes permisos para eliminar esta tarea"
    )

# ============================================================================
# ✅ ENDPOINTS PARA GESTIONAR EL HISTORIAL (RECORD)
# ============================================================================

@router.post("/{task_id}/records", response_model=TaskOut)
def add_task_record(
    task_id: int,
    record_data: TaskRecordAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Agregar una entrada al historial de la tarea
    
    Permisos:
    - Administrador: ✅ Puede agregar en cualquier tarea
    - Manager: ✅ Puede agregar en tareas de sus tableros
    - Supervisor: ✅ Puede agregar en tareas de tableros asignados
    - Agente: ✅ Puede agregar en sus tareas asignadas
    - Visualizador: ❌ No puede agregar
    """
    print(f"\n{'='*80}")
    print(f"📝 ADD TASK RECORD - Task ID: {task_id}")
    print(f"📝 Usuario: {current_user.username} ({current_user.role.name if current_user.role else 'Sin rol'})")
    print(f"📝 Comentario: {record_data.doc}")
    
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        print(f"❌ Tarea no encontrada")
        print(f"{'='*80}\n")
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    # Verificar permisos
    if not PermissionChecker.can_add_record(current_user, task, db):
        print(f"❌ Sin permisos para agregar comentario")
        print(f"{'='*80}\n")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para agregar comentarios a esta tarea"
        )
    
    # Obtener el estado actual de la tarea
    state_name = task.state.name if task.state else "Sin estado"
    
    # Agregar entrada al historial
    add_record_entry(task, current_user, state_name, record_data.doc)
    
    db.commit()
    db.refresh(task)
    
    print(f"✅ Comentario agregado exitosamente")
    print(f"{'='*80}\n")
    
    return TaskOut.model_validate(task)

@router.get("/{task_id}/records", response_model=List[Dict])
def get_task_records(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener el historial completo de una tarea
    
    Todos los roles que pueden ver la tarea pueden ver su historial
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    # Verificar si puede ver la tarea
    board = db.query(Board).filter(Board.id == task.board_id).first()
    if not PermissionChecker.can_view_board(current_user, board, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver esta tarea"
        )
    
    # Retornar el historial (si es None, retornar lista vacía)
    return task.record if task.record else []