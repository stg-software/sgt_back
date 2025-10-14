# app/api/boards.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.board import Board
from app.models.board_assignment import BoardAssignment
from app.models.task import Task
from app.schemas.board import BoardCreate, BoardOut, BoardAssignmentCreate
from app.schemas.task import TaskOut, TaskCreate
from app.api.auth import get_current_user
from app.models.user import User
from app.models.workflow import WorkflowState
from app.schemas.workflow import WorkflowStateOutLight
from app.core.permissions import PermissionChecker
from datetime import datetime


router = APIRouter(prefix="/boards", tags=["Boards"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[BoardOut])
def list_boards(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Listar tableros accesibles para el usuario según su rol"""
    boards = PermissionChecker.get_user_boards(current_user, db)
    return boards

# Fragmento relevante de app/api/boards.py

@router.post("/", response_model=BoardOut, status_code=status.HTTP_201_CREATED)
def create_board(
    data: BoardCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Crear un nuevo tablero (solo Administrador y Manager)"""
    
    role_name = current_user.role.name if current_user.role else None
    
    # ✅ CORRECTO: Solo Admin y Manager pueden crear tableros
    if role_name not in ["Administrador", "Manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Solo Administrador y Manager pueden crear tableros. Tu rol: {role_name}"
        )
    
    print(f"✅ Usuario {current_user.username} ({role_name}) creando tablero")
    
    # Crear el tablero
    board = Board(
        name=data.name, 
        template_id=data.template_id,
        description=data.description,
        color=data.color,
        owner_id=current_user.id
    )
    db.add(board)
    db.commit()
    db.refresh(board)
    
    print(f"✅ Tablero '{board.name}' creado con ID {board.id}")
    
    # ✅ NUEVO: Asignar usuarios al tablero si se proporcionaron
    if data.assigned_user_ids and len(data.assigned_user_ids) > 0:
        print(f"📋 Asignando {len(data.assigned_user_ids)} usuarios al tablero...")
        
        for user_id in data.assigned_user_ids:
            # Verificar que el usuario existe
            user_exists = db.query(User).filter(User.id == user_id).first()
            if not user_exists:
                print(f"⚠️ Usuario con ID {user_id} no encontrado, saltando...")
                continue
            
            # Verificar que no sea el owner (no tiene sentido asignarlo)
            if user_id == current_user.id:
                print(f"⚠️ Saltando owner {user_id} (ya es propietario)")
                continue
            
            # Crear la asignación
            assignment = BoardAssignment(
                board_id=board.id,
                user_id=user_id
            )
            db.add(assignment)
            print(f"  ✅ Usuario {user_id} asignado")
        
        db.commit()
        db.refresh(board)
        print(f"✅ Asignaciones completadas para tablero {board.id}")
    
    return board

@router.get("/{board_id}", response_model=BoardOut)
def get_board(
    board_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Obtener un tablero específico"""
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    
    if not PermissionChecker.can_view_board(current_user, board, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver este tablero"
        )
    
    return board

@router.put("/{board_id}", response_model=BoardOut)
def update_board(
    board_id: int, 
    data: BoardCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Actualizar un tablero"""
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    
    if not PermissionChecker.can_edit_board(current_user, board, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para editar este tablero"
        )
    
    board.name = data.name
    board.template_id = data.template_id
    if data.description is not None:
        board.description = data.description
    if data.color is not None:
        board.color = data.color
    
    db.commit()
    db.refresh(board)
    return board

@router.delete("/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_board(
    board_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Eliminar un tablero (solo Admin u Owner)"""
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    
    # ✅ CORRECTO: Solo Admin o Owner pueden eliminar
    if not (PermissionChecker.is_admin(current_user) or board.owner_id == current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el administrador o el propietario pueden eliminar este tablero"
        )
    
    db.delete(board)
    db.commit()
    return

# ============================================================================
# ENDPOINTS DE ASIGNACIÓN DE USUARIOS A TABLEROS
# ============================================================================

@router.post("/{board_id}/assign", status_code=status.HTTP_201_CREATED)
def assign_user_to_board(
    board_id: int,
    assignment: BoardAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Asignar un usuario a un tablero
    
    Permisos según matriz:
    - Administrador: Puede asignar en TODOS los tableros
    - Manager: Solo en tableros donde es OWNER
    - Supervisor: Solo en tableros donde está ASIGNADO
    """
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    
    role_name = current_user.role.name if current_user.role else None
    
    # ✅ CORRECCIÓN: Validación según matriz de permisos
    can_assign = False
    
    # Admin puede asignar en TODOS los tableros
    if PermissionChecker.is_admin(current_user):
        can_assign = True
        print(f"✅ Admin {current_user.username} asignando usuario al tablero {board_id}")
    
    # Manager SOLO si es owner del tablero
    elif role_name == "Manager":
        if board.owner_id == current_user.id:
            can_assign = True
            print(f"✅ Manager {current_user.username} (owner) asignando usuario a su tablero {board_id}")
        else:
            print(f"❌ Manager {current_user.username} NO es owner del tablero {board_id}")
    
    # Supervisor SOLO si está asignado al tablero
    elif role_name == "Supervisor":
        is_assigned = db.query(BoardAssignment).filter(
            BoardAssignment.board_id == board_id,
            BoardAssignment.user_id == current_user.id
        ).first()
        
        if is_assigned:
            can_assign = True
            print(f"✅ Supervisor {current_user.username} (asignado) asignando usuario al tablero {board_id}")
        else:
            print(f"❌ Supervisor {current_user.username} NO está asignado al tablero {board_id}")
    
    if not can_assign:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"No tienes permisos para asignar usuarios a este tablero. Tu rol: {role_name}"
        )
    
    # Verificar si ya está asignado
    existing = db.query(BoardAssignment).filter(
        BoardAssignment.board_id == board_id,
        BoardAssignment.user_id == assignment.user_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Usuario ya asignado a este tablero")
    
    # Crear asignación
    new_assignment = BoardAssignment(
        board_id=board_id,
        user_id=assignment.user_id
    )
    db.add(new_assignment)
    db.commit()
    
    return {"message": "Usuario asignado exitosamente"}

@router.delete("/{board_id}/assign/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_user_from_board(
    board_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Remover un usuario de un tablero
    
    Mismos permisos que asignación:
    - Administrador: Puede remover de TODOS los tableros
    - Manager: Solo de tableros donde es OWNER
    - Supervisor: Solo de tableros donde está ASIGNADO
    """
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    
    role_name = current_user.role.name if current_user.role else None
    
    # ✅ Misma lógica que assign
    can_remove = False
    
    if PermissionChecker.is_admin(current_user):
        can_remove = True
    elif role_name == "Manager" and board.owner_id == current_user.id:
        can_remove = True
    elif role_name == "Supervisor":
        is_assigned = db.query(BoardAssignment).filter(
            BoardAssignment.board_id == board_id,
            BoardAssignment.user_id == current_user.id
        ).first()
        if is_assigned:
            can_remove = True
    
    if not can_remove:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"No tienes permisos para remover usuarios de este tablero. Tu rol: {role_name}"
        )
    
    assignment = db.query(BoardAssignment).filter(
        BoardAssignment.board_id == board_id,
        BoardAssignment.user_id == user_id
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    
    db.delete(assignment)
    db.commit()
    return

# ============================================================================
# ENDPOINTS DE TAREAS
# ============================================================================

@router.get("/{board_id}/tasks", response_model=List[TaskOut])
def get_board_tasks(
    board_id: int,
    start_date: str = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    end_date: str = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener tareas de un tablero según permisos del usuario
    
    - **board_id**: ID del tablero
    - **start_date**: Filtrar tareas creadas desde esta fecha (opcional)
    - **end_date**: Filtrar tareas creadas hasta esta fecha (opcional)
    """
    
    # Verificar que el tablero existe
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    
    # Verificar permisos de visualización del tablero
    if not PermissionChecker.can_view_board(current_user, board, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver este tablero"
        )
    
    # ✅ Parsear fechas si se proporcionan
    from datetime import datetime
    parsed_start_date = None
    parsed_end_date = None
    
    if start_date:
        try:
            parsed_start_date = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Formato de start_date inválido (use YYYY-MM-DD)"
            )
    
    if end_date:
        try:
            parsed_end_date = datetime.strptime(end_date, "%Y-%m-%d")
            # Agregar 23:59:59 para incluir todo el día
            parsed_end_date = parsed_end_date.replace(hour=23, minute=59, second=59)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Formato de end_date inválido (use YYYY-MM-DD)"
            )
    
    # ✅ Filtrar tareas según el rol
    role_name = current_user.role.name if current_user.role else None
    
    print(f"\n{'='*80}")
    print(f"🔍 GET TASKS - Usuario: {current_user.username} ({role_name})")
    print(f"🔍 GET TASKS - Board ID: {board_id}")
    print(f"🔍 GET TASKS - Filtros: start={start_date}, end={end_date}")
    
    # Query base
    query = db.query(Task).filter(Task.board_id == board_id)
    
    # Aplicar filtros de fecha
    if parsed_start_date:
        query = query.filter(Task.created_at >= parsed_start_date)
    if parsed_end_date:
        query = query.filter(Task.created_at <= parsed_end_date)
    
    # Administrador, Manager, Supervisor: ven todas las tareas del tablero
    if role_name in ["Administrador", "Manager", "Supervisor"]:
        tasks = query.all()
        print(f"✅ {role_name}: ve {len(tasks)} tareas del tablero")
        print(f"{'='*80}\n")
        return tasks
    
    # ✅ Agente: SOLO ve tareas asignadas a él
    elif role_name == "Agente":
        tasks = query.filter(Task.assigned_to_id == current_user.id).all()
        print(f"✅ Agente: ve solo {len(tasks)} tareas asignadas a él")
        for task in tasks:
            print(f"   - Tarea #{task.id}: {task.title} (assigned_to_id={task.assigned_to_id})")
        print(f"{'='*80}\n")
        return tasks
    
    # Visualizador: ve todas las tareas (solo lectura)
    elif role_name == "Visualizador":
        tasks = query.all()
        print(f"✅ Visualizador: ve todas las {len(tasks)} tareas (solo lectura)")
        print(f"{'='*80}\n")
        return tasks
    
    # Por defecto, no mostrar tareas
    print(f"⚠️ Usuario sin rol válido: no ve tareas")
    print(f"{'='*80}\n")
    return []

@router.post("/{board_id}/tasks", response_model=TaskOut)
def create_task_for_board(
    board_id: int,
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Crear tarea en un tablero (solo Admin, Manager, Supervisor)"""
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    
    if not PermissionChecker.can_view_board(current_user, board, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para acceder a este tablero"
        )
    
    role_name = current_user.role.name if current_user.role else None
    
    if role_name not in ["Administrador", "Manager", "Supervisor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Solo Administrador, Manager y Supervisor pueden crear tareas. Tu rol: {role_name}"
        )
    
    print(f"✅ Usuario {current_user.username} ({role_name}) creando tarea en tablero {board_id}")
    
    # Verificar que el state_id pertenece al workflow del board
    state = db.query(WorkflowState).filter(
        WorkflowState.id == task.state_id,
        WorkflowState.workflow_id == board.template_id
    ).first()
    
    if not state:
        raise HTTPException(
            status_code=400, 
            detail="El estado no pertenece a la plantilla del tablero"
        )
    
    # Verificar que assigned_to_id es válido si se proporciona
    if task.assigned_to_id is not None:
        assigned_user = db.query(User).filter(User.id == task.assigned_to_id).first()
        if not assigned_user:
            raise HTTPException(
                status_code=400,
                detail=f"El usuario con ID {task.assigned_to_id} no existe"
            )
    
    # ✅ NUEVO: Crear registro inicial
    now = datetime.now()
    initial_record = [{
        "fecha": now.strftime("%d/%m/%Y"),
        "hora": now.strftime("%H:%M:%S"),
        "user": current_user.username,
        "status": state.name,
        "doc": f"Tarea creada por {current_user.username}"
    }]
    
    # Crear la tarea
    db_task = Task(
        title=task.title,
        description=task.description,
        board_id=board_id,
        state_id=task.state_id,
        assigned_to_id=task.assigned_to_id,
        created_by_id=current_user.id,
        start_date=task.start_date,
        end_date=task.end_date,
        custom_fields=task.custom_fields or {},
        record=initial_record  # ✅ NUEVO: Inicializar con registro de creación
    )
    
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    print(f"✅ Tarea '{db_task.title}' creada con ID {db_task.id}, assigned_to_id={db_task.assigned_to_id}")
    
    return db_task

@router.get("/{board_id}/states", response_model=List[WorkflowStateOutLight])
def get_board_states(
    board_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Obtener estados disponibles para un tablero"""
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    
    states = db.query(WorkflowState).filter(
        WorkflowState.workflow_id == board.template_id
    ).order_by(WorkflowState.order).all()

    return states