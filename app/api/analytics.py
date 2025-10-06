# app/api/analytics.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from app.core.database import SessionLocal
from app.models.board import Board
from app.api.auth import get_current_user
from app.models.user import User
from app.core.permissions import PermissionChecker
from app.services.analytics_service import AnalyticsService
from app.schemas.analytics import BoardAnalyticsResponse

# ✅ Esta línea es CRÍTICA - debe estar al inicio
router = APIRouter(prefix="/analytics", tags=["Analytics"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/boards/{board_id}", response_model=BoardAnalyticsResponse)
def get_board_analytics(
    board_id: int,
    days: int = Query(30, ge=7, le=365, description="Días de historia para análisis"),
    start_date: Optional[str] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener analytics completo de un tablero con filtros de fecha
    
    - **board_id**: ID del tablero
    - **days**: Días de historia (default: 30, min: 7, max: 365)
    - **start_date**: Fecha de inicio del filtro (opcional, formato: YYYY-MM-DD)
    - **end_date**: Fecha de fin del filtro (opcional, formato: YYYY-MM-DD)
    """
    
    # Verificar que el tablero existe
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        raise HTTPException(status_code=404, detail="Tablero no encontrado")
    
    # Verificar permisos
    if not PermissionChecker.can_view_board(current_user, board, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver este tablero"
        )
    
    # Parsear fechas si se proporcionan
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
    
    # Validar que start_date no sea mayor que end_date
    if parsed_start_date and parsed_end_date and parsed_start_date > parsed_end_date:
        raise HTTPException(
            status_code=400,
            detail="La fecha de inicio no puede ser mayor que la fecha de fin"
        )
    
    # Calcular métricas
    overview = AnalyticsService.get_board_overview(board_id, db)
    productivity = AnalyticsService.get_productivity_metrics(board_id, db, days)
    bottlenecks = AnalyticsService.get_bottlenecks(board_id, db)
    workload = AnalyticsService.get_workload_distribution(board_id, db)
    time_in_states = AnalyticsService.get_time_in_states(board_id, db)
    tasks_by_state = AnalyticsService.get_tasks_by_state(
        board_id, 
        db, 
        parsed_start_date, 
        parsed_end_date
    )
    
    # Tendencias
    daily_trends = AnalyticsService.get_daily_trends(board_id, db, min(days, 90))
    
    return {
        "overview": overview,
        "productivity": productivity,
        "bottlenecks": bottlenecks,
        "workload": workload,
        "time_in_states": time_in_states,
        "tasks_by_state": tasks_by_state,
        "trends": {
            "daily": daily_trends
        }
    }