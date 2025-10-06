# app/services/analytics_service.py
from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_, or_
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from app.models.task import Task
from app.models.board import Board
from app.models.workflow import WorkflowState
from app.models.user import User

class AnalyticsService:
    """Servicio para calcular métricas y estadísticas de tableros"""
    
    @staticmethod
    def get_board_overview(board_id: int, db: Session) -> Dict[str, Any]:
        """Resumen general del tablero"""
        
        # Total de tareas
        total_tasks = db.query(Task).filter(Task.board_id == board_id).count()
        
        # Obtener estados del workflow
        board = db.query(Board).filter(Board.id == board_id).first()
        if not board:
            return {}
        
        states = db.query(WorkflowState).filter(
            WorkflowState.workflow_id == board.template_id
        ).order_by(WorkflowState.order).all()
        
        # Identificar estado final (último en el orden)
        final_state_id = states[-1].id if states else None
        
        # Tareas completadas (en el último estado)
        completed = db.query(Task).filter(
            Task.board_id == board_id,
            Task.state_id == final_state_id
        ).count() if final_state_id else 0
        
        # Tareas en progreso (no en estado inicial ni final)
        initial_state_id = states[0].id if states else None
        in_progress = db.query(Task).filter(
            Task.board_id == board_id,
            Task.state_id != final_state_id,
            Task.state_id != initial_state_id
        ).count() if len(states) > 1 else 0
        
        # Tareas vencidas (con end_date pasado y no completadas)
        now = datetime.utcnow()
        overdue = db.query(Task).filter(
            Task.board_id == board_id,
            Task.state_id != final_state_id,
            Task.end_date < now
        ).count() if final_state_id else 0
        
        # Tasa de completado
        completion_rate = (completed / total_tasks * 100) if total_tasks > 0 else 0
        
        return {
            "total_tasks": total_tasks,
            "completed": completed,
            "in_progress": in_progress,
            "overdue": overdue,
            "pending": total_tasks - completed - in_progress,
            "completion_rate": round(completion_rate, 1)
        }
    
    @staticmethod
    def get_productivity_metrics(
        board_id: int, 
        db: Session, 
        days: int = 30
    ) -> Dict[str, Any]:
        """Métricas de productividad"""
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Obtener estado final
        board = db.query(Board).filter(Board.id == board_id).first()
        if not board:
            return {}
        
        states = db.query(WorkflowState).filter(
            WorkflowState.workflow_id == board.template_id
        ).order_by(WorkflowState.order).all()
        
        final_state_id = states[-1].id if states else None
        
        # Tareas completadas en el periodo
        completed_tasks = db.query(Task).filter(
            Task.board_id == board_id,
            Task.state_id == final_state_id,
            Task.updated_at >= start_date
        ).all()
        
        # Calcular tiempo promedio de completado
        completion_times = []
        for task in completed_tasks:
            if task.created_at and task.updated_at:
                delta = task.updated_at - task.created_at
                completion_times.append(delta.total_seconds() / 3600)  # horas
        
        avg_completion_time = sum(completion_times) / len(completion_times) if completion_times else 0
        
        # Tareas por día
        tasks_per_day = len(completed_tasks) / days if days > 0 else 0
        
        # Velocidad semanal (últimas 2 semanas para comparar)
        week_ago = datetime.utcnow() - timedelta(days=7)
        two_weeks_ago = datetime.utcnow() - timedelta(days=14)
        
        this_week = db.query(Task).filter(
            Task.board_id == board_id,
            Task.state_id == final_state_id,
            Task.updated_at >= week_ago
        ).count()
        
        last_week = db.query(Task).filter(
            Task.board_id == board_id,
            Task.state_id == final_state_id,
            Task.updated_at >= two_weeks_ago,
            Task.updated_at < week_ago
        ).count()
        
        velocity_trend = ((this_week - last_week) / last_week * 100) if last_week > 0 else 0
        
        return {
            "tasks_per_day": round(tasks_per_day, 2),
            "avg_completion_time_hours": round(avg_completion_time, 1),
            "avg_completion_time_days": round(avg_completion_time / 24, 1),
            "velocity": {
                "this_week": this_week,
                "last_week": last_week,
                "trend_percent": round(velocity_trend, 1)
            },
            "completed_in_period": len(completed_tasks)
        }
    
    @staticmethod
    def get_bottlenecks(board_id: int, db: Session) -> List[Dict[str, Any]]:
        """Detectar cuellos de botella por estado"""
        
        board = db.query(Board).filter(Board.id == board_id).first()
        if not board:
            return []
        
        states = db.query(WorkflowState).filter(
            WorkflowState.workflow_id == board.template_id
        ).order_by(WorkflowState.order).all()
        
        bottlenecks = []
        
        for state in states:
            # Contar tareas en este estado
            tasks_in_state = db.query(Task).filter(
                Task.board_id == board_id,
                Task.state_id == state.id
            ).all()
            
            if not tasks_in_state:
                continue
            
            # Calcular tiempo promedio en este estado
            times = []
            for task in tasks_in_state:
                if task.updated_at and task.created_at:
                    # Aproximación: diferencia entre created_at y updated_at
                    delta = datetime.utcnow() - task.updated_at
                    times.append(delta.total_seconds() / 3600)  # horas
            
            avg_time = sum(times) / len(times) if times else 0
            
            # Determinar severidad
            severity = "low"
            if len(tasks_in_state) > 10 and avg_time > 48:
                severity = "high"
            elif len(tasks_in_state) > 5 or avg_time > 24:
                severity = "medium"
            
            bottlenecks.append({
                "state_id": state.id,
                "state_name": state.name,
                "state_order": state.order,
                "tasks_count": len(tasks_in_state),
                "avg_time_hours": round(avg_time, 1),
                "avg_time_days": round(avg_time / 24, 1),
                "severity": severity
            })
        
        # Ordenar por severidad y cantidad de tareas
        severity_order = {"high": 0, "medium": 1, "low": 2}
        bottlenecks.sort(key=lambda x: (severity_order[x["severity"]], -x["tasks_count"]))
        
        return bottlenecks
    
    @staticmethod
    def get_workload_distribution(board_id: int, db: Session) -> List[Dict[str, Any]]:
        """Distribución de carga de trabajo por usuario"""
        
        # Obtener todos los usuarios asignados al tablero
        board = db.query(Board).filter(Board.id == board_id).first()
        if not board:
            return []
        
        # Obtener estado final
        states = db.query(WorkflowState).filter(
            WorkflowState.workflow_id == board.template_id
        ).order_by(WorkflowState.order).all()
        
        final_state_id = states[-1].id if states else None
        
        # Tareas por usuario
        workload = []
        
        # Obtener usuarios únicos asignados a tareas
        assigned_users = db.query(Task.assigned_to_id).filter(
            Task.board_id == board_id,
            Task.assigned_to_id.isnot(None)
        ).distinct().all()
        
        for (user_id,) in assigned_users:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                continue
            
            # Tareas asignadas (no completadas)
            assigned_tasks = db.query(Task).filter(
                Task.board_id == board_id,
                Task.assigned_to_id == user_id,
                Task.state_id != final_state_id
            ).count()
            
            # Tareas completadas esta semana
            week_ago = datetime.utcnow() - timedelta(days=7)
            completed_this_week = db.query(Task).filter(
                Task.board_id == board_id,
                Task.assigned_to_id == user_id,
                Task.state_id == final_state_id,
                Task.updated_at >= week_ago
            ).count()
            
            # Tiempo promedio de completado
            completed_tasks = db.query(Task).filter(
                Task.board_id == board_id,
                Task.assigned_to_id == user_id,
                Task.state_id == final_state_id
            ).all()
            
            completion_times = []
            for task in completed_tasks:
                if task.created_at and task.updated_at:
                    delta = task.updated_at - task.created_at
                    completion_times.append(delta.total_seconds() / 3600)
            
            avg_completion = sum(completion_times) / len(completion_times) if completion_times else 0
            
            # Determinar estado de carga
            status = "balanced"
            if assigned_tasks > 15:
                status = "overloaded"
            elif assigned_tasks < 3 and assigned_tasks > 0:
                status = "underutilized"
            elif assigned_tasks == 0:
                status = "idle"
            
            workload.append({
                "user_id": user.id,
                "username": user.username,
                "full_name": f"{user.first_name} {user.last_name}",
                "assigned_tasks": assigned_tasks,
                "completed_this_week": completed_this_week,
                "avg_completion_time_hours": round(avg_completion, 1),
                "avg_completion_time_days": round(avg_completion / 24, 1),
                "status": status
            })
        
        # Ordenar por carga de trabajo
        workload.sort(key=lambda x: x["assigned_tasks"], reverse=True)
        
        return workload
    
    @staticmethod
    def get_time_in_states(board_id: int, db: Session) -> Dict[str, Dict[str, Any]]:
        """Tiempo promedio que las tareas pasan en cada estado"""
        
        board = db.query(Board).filter(Board.id == board_id).first()
        if not board:
            return {}
        
        states = db.query(WorkflowState).filter(
            WorkflowState.workflow_id == board.template_id
        ).order_by(WorkflowState.order).all()
        
        time_in_states = {}
        
        for state in states:
            tasks_in_state = db.query(Task).filter(
                Task.board_id == board_id,
                Task.state_id == state.id
            ).all()
            
            times = []
            for task in tasks_in_state:
                if task.updated_at:
                    delta = datetime.utcnow() - task.updated_at
                    times.append(delta.total_seconds() / 3600)
            
            avg_time = sum(times) / len(times) if times else 0
            
            time_in_states[state.name] = {
                "avg_hours": round(avg_time, 1),
                "avg_days": round(avg_time / 24, 1),
                "tasks_count": len(tasks_in_state),
                "state_order": state.order
            }
        
        return time_in_states
    
    @staticmethod
    def get_daily_trends(board_id: int, db: Session, days: int = 30) -> List[Dict[str, Any]]:
        """Tendencia diaria de creación y completado de tareas"""
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        board = db.query(Board).filter(Board.id == board_id).first()
        if not board:
            return []
        
        states = db.query(WorkflowState).filter(
            WorkflowState.workflow_id == board.template_id
        ).order_by(WorkflowState.order).all()
        
        final_state_id = states[-1].id if states else None
        
        trends = []
        
        for i in range(days):
            date = start_date + timedelta(days=i)
            next_date = date + timedelta(days=1)
            
            # Tareas creadas ese día
            created = db.query(Task).filter(
                Task.board_id == board_id,
                Task.created_at >= date,
                Task.created_at < next_date
            ).count()
            
            # Tareas completadas ese día
            completed = db.query(Task).filter(
                Task.board_id == board_id,
                Task.state_id == final_state_id,
                Task.updated_at >= date,
                Task.updated_at < next_date
            ).count() if final_state_id else 0
            
            trends.append({
                "date": date.strftime("%Y-%m-%d"),
                "created": created,
                "completed": completed,
                "net": created - completed
            })
        
        return trends
    
    @staticmethod
    def get_tasks_by_state(board_id: int, db: Session, start_date: datetime = None, end_date: datetime = None) -> List[Dict[str, Any]]:
        """Obtener distribución de tareas por estado del workflow"""
        
        board = db.query(Board).filter(Board.id == board_id).first()
        if not board:
            return []
        
        states = db.query(WorkflowState).filter(
            WorkflowState.workflow_id == board.template_id
        ).order_by(WorkflowState.order).all()
        
        tasks_by_state = []
        
        for state in states:
            # Query base
            query = db.query(Task).filter(
                Task.board_id == board_id,
                Task.state_id == state.id
            )
            
            # Aplicar filtros de fecha si existen
            if start_date:
                query = query.filter(Task.created_at >= start_date)
            if end_date:
                query = query.filter(Task.created_at <= end_date)
            
            count = query.count()
            
            tasks_by_state.append({
                "state_id": state.id,
                "state_name": state.name,
                "state_order": state.order,
                "tasks_count": count
            })
        
        return tasks_by_state