# app/schemas/analytics.py
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class OverviewMetrics(BaseModel):
    total_tasks: int
    completed: int
    in_progress: int
    overdue: int
    pending: int
    completion_rate: float

class VelocityMetrics(BaseModel):
    this_week: int
    last_week: int
    trend_percent: float

class ProductivityMetrics(BaseModel):
    tasks_per_day: float
    avg_completion_time_hours: float
    avg_completion_time_days: float
    velocity: VelocityMetrics
    completed_in_period: int

class BottleneckInfo(BaseModel):
    state_id: int
    state_name: str
    state_order: int
    tasks_count: int
    avg_time_hours: float
    avg_time_days: float
    severity: str

class WorkloadInfo(BaseModel):
    user_id: int
    username: str
    full_name: str
    assigned_tasks: int
    completed_this_week: int
    avg_completion_time_hours: float
    avg_completion_time_days: float
    status: str

class StateTimeInfo(BaseModel):
    avg_hours: float
    avg_days: float
    tasks_count: int
    state_order: int

class DailyTrend(BaseModel):
    date: str
    created: int
    completed: int
    net: int

class TasksByState(BaseModel):
    state_id: int
    state_name: str
    state_order: int
    tasks_count: int

# Actualizar BoardAnalyticsResponse
class BoardAnalyticsResponse(BaseModel):
    overview: OverviewMetrics
    productivity: ProductivityMetrics
    bottlenecks: List[BottleneckInfo]
    workload: List[WorkloadInfo]
    time_in_states: Dict[str, StateTimeInfo]
    tasks_by_state: List[TasksByState]  # ✅ NUEVO
    trends: Dict[str, List[DailyTrend]]
    
    class Config:
        from_attributes = True
