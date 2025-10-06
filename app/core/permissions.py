# app/core/permissions.py
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.board import Board
from app.models.task import Task
from app.models.board_assignment import BoardAssignment

class PermissionChecker:
    """Helper para verificar permisos de usuario según matriz de permisos"""
    
    @staticmethod
    def is_admin(user: User) -> bool:
        """Verificar si el usuario es administrador"""
        return user.role and user.role.name == "Administrador"
    
    @staticmethod
    def can_view_board(user: User, board: Board, db: Session) -> bool:
        """
        Verificar si el usuario puede ver un tablero
        
        Según matriz:
        - Administrador: ✅ TODOS los tableros
        - Manager: ✅ Tableros donde es owner o está asignado
        - Supervisor: ✅ Tableros donde está asignado
        - Agente: ✅ Tableros donde está asignado
        - Visualizador: ✅ Tableros donde está asignado
        """
        # Admin puede ver todo
        if PermissionChecker.is_admin(user):
            return True
        
        # Owner puede ver su tablero
        if board.owner_id == user.id:
            return True
        
        # Verificar si está asignado al tablero
        assignment = db.query(BoardAssignment).filter(
            BoardAssignment.board_id == board.id,
            BoardAssignment.user_id == user.id
        ).first()
        
        return assignment is not None
    
    @staticmethod
    def can_edit_board(user: User, board: Board, db: Session) -> bool:
        """
        Verificar si el usuario puede editar un tablero
        
        Según matriz:
        - Administrador: ✅ TODOS los tableros
        - Manager: ✅ Solo tableros donde es owner o está asignado
        - Supervisor: ❌ NO puede editar tableros
        - Agente: ❌ NO puede editar tableros
        - Visualizador: ❌ NO puede editar tableros
        """
        role_name = user.role.name if user.role else None
        
        # Admin puede editar todo
        if role_name == "Administrador":
            return True
        
        # Manager puede editar si es owner O está asignado
        if role_name == "Manager":
            # Si es owner
            if board.owner_id == user.id:
                return True
            
            # Si está asignado
            assignment = db.query(BoardAssignment).filter(
                BoardAssignment.board_id == board.id,
                BoardAssignment.user_id == user.id
            ).first()
            return assignment is not None
        
        # Supervisor, Agente y Visualizador NO pueden editar tableros
        return False
    
    @staticmethod
    def can_edit_task(user: User, task: Task, db: Session) -> bool:
        """
        Verificar si el usuario puede editar una tarea
        
        Según matriz:
        - Administrador: ✅ TODAS las tareas, todos los campos
        - Manager: ✅ Tareas de sus tableros, todos los campos
        - Supervisor: ✅ Tareas de tableros asignados, todos los campos
        - Agente: ⚠️ SOLO sus tareas asignadas, SOLO record/estado
        - Visualizador: ❌ NO puede editar
        """
        role_name = user.role.name if user.role else None
        
        # Admin puede editar todo
        if role_name == "Administrador":
            return True
        
        # Visualizador no puede editar nada
        if role_name == "Visualizador":
            return False
        
        # Verificar si está asignado al tablero
        assignment = db.query(BoardAssignment).filter(
            BoardAssignment.board_id == task.board_id,
            BoardAssignment.user_id == user.id
        ).first()
        
        # Si no está asignado al tablero, verificar si es owner
        from app.models.board import Board
        board = db.query(Board).filter(Board.id == task.board_id).first()
        
        is_board_member = assignment is not None or (board and board.owner_id == user.id)
        
        if not is_board_member:
            return False
        
        # Manager puede editar tareas en tableros donde es owner o está asignado
        if role_name == "Manager":
            return True
        
        # Supervisor puede editar tareas en tableros asignados
        if role_name == "Supervisor":
            return True
        
        # Agente solo puede editar tareas asignadas a él
        if role_name == "Agente":
            return task.assigned_to_id == user.id
        
        return False
    
    @staticmethod
    def get_editable_task_fields(user: User, task: Task) -> list:
        """
        Obtener campos editables según el rol
        
        Según matriz ACTUALIZADA:
        - Administrador: TODOS los campos (incluye fechas)
        - Manager: TODOS los campos (incluye fechas)
        - Supervisor: TODOS los campos (incluye fechas)
        - Agente: ⚠️ SOLO estado (NO descripción ni fechas)
        - Visualizador: NINGUNO
        """
        role_name = user.role.name if user.role else None
        
        # Campos que NUNCA se pueden editar
        readonly_fields = ["id", "created_at", "updated_at", "created_by_id", "created_by", "board_id"]
        
        # Admin, Manager y Supervisor pueden editar todos los campos incluidas las fechas
        if role_name in ["Administrador", "Manager", "Supervisor"]:
            return ["title", "description", "state_id", "assigned_to_id", "start_date", "end_date", "custom_fields"]
        
        # ✅ ACTUALIZADO: Agente solo puede editar estado (state_id)
        # El record se maneja por endpoint separado
        if role_name == "Agente":
            return ["state_id"]
        
        # Visualizador no puede editar nada
        return []
    
    @staticmethod
    def can_add_record(user: User, task: Task, db: Session) -> bool:
        """
        ✅ NUEVO: Verificar si puede agregar entradas al historial (record)
        
        Según matriz:
        - Administrador: ✅ Puede agregar en cualquier tarea
        - Manager: ✅ Puede agregar en tareas de sus tableros
        - Supervisor: ✅ Puede agregar en tareas de tableros asignados
        - Agente: ✅ Puede agregar en sus tareas asignadas
        - Visualizador: ❌ No puede agregar
        """
        role_name = user.role.name if user.role else None
        
        # Admin puede agregar en cualquier tarea
        if role_name == "Administrador":
            return True
        
        # Visualizador no puede agregar
        if role_name == "Visualizador":
            return False
        
        # Verificar si está asignado al tablero
        assignment = db.query(BoardAssignment).filter(
            BoardAssignment.board_id == task.board_id,
            BoardAssignment.user_id == user.id
        ).first()
        
        # Si no está asignado al tablero, verificar si es owner
        from app.models.board import Board
        board = db.query(Board).filter(Board.id == task.board_id).first()
        
        is_board_member = assignment is not None or (board and board.owner_id == user.id)
        
        if not is_board_member:
            return False
        
        # Manager puede agregar en tareas de sus tableros
        if role_name == "Manager":
            return True
        
        # Supervisor puede agregar en tareas de tableros asignados
        if role_name == "Supervisor":
            return True
        
        # Agente solo puede agregar en tareas asignadas a él
        if role_name == "Agente":
            return task.assigned_to_id == user.id
        
        return False
    
    @staticmethod
    def get_user_boards(user: User, db: Session) -> list:
        """
        Obtener tableros accesibles para el usuario
        
        Según matriz:
        - Administrador: ✅ TODOS los tableros
        - Manager: ✅ Tableros donde es owner o está asignado
        - Supervisor: ✅ Tableros donde está asignado
        - Agente: ✅ Tableros donde está asignado
        - Visualizador: ✅ Tableros donde está asignado
        """
        from app.models.board import Board
        
        # Admin ve todos los tableros
        if PermissionChecker.is_admin(user):
            return db.query(Board).filter(Board.is_archived == False).all()
        
        # Obtener tableros donde el usuario es owner
        owned_boards = db.query(Board).filter(
            Board.owner_id == user.id,
            Board.is_archived == False
        ).all()
        
        # Obtener tableros donde está asignado
        assigned_board_ids = db.query(BoardAssignment.board_id).filter(
            BoardAssignment.user_id == user.id
        ).all()
        assigned_board_ids = [b[0] for b in assigned_board_ids]
        
        assigned_boards = db.query(Board).filter(
            Board.id.in_(assigned_board_ids),
            Board.is_archived == False
        ).all()
        
        # Combinar y eliminar duplicados
        all_boards = {b.id: b for b in owned_boards + assigned_boards}
        return list(all_boards.values())