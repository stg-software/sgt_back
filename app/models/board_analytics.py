# app/models/board_analytics.py
from sqlalchemy import Column, Integer, ForeignKey, DateTime, JSON, Date
from sqlalchemy.sql import func
from app.core.database import Base

class BoardAnalyticsSnapshot(Base):
    """
    Snapshots diarios de métricas del tablero para análisis histórico.
    Permite generar gráficos de tendencias sin recalcular todo el historial.
    """
    __tablename__ = "board_analytics_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    board_id = Column(Integer, ForeignKey("boards.id", ondelete="CASCADE"), nullable=False, index=True)
    snapshot_date = Column(Date, nullable=False, index=True)
    
    # Métricas en JSON para flexibilidad
    metrics = Column(JSON, nullable=False)
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Índice compuesto para búsquedas rápidas
    __table_args__ = (
        {"extend_existing": True}
    )