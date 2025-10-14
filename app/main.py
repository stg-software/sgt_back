# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
from sqlalchemy import text
from app.api import tasks, workflow, roles, users, auth, boards, task_fields, analytics
from app.core.database import Base, engine, SessionLocal

app = FastAPI(title="SGT_v1 - Backend")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://sgt-frontend-production.s3-website.us-east-2.amazonaws.com",  # S3 Production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Crear tablas si no existen
Base.metadata.create_all(bind=engine)

# Health Check Endpoint (para CI/CD)
@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint para CI/CD"""
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "database": "connected"
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )

# Routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(workflow.router, prefix="/api/v1")
app.include_router(roles.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(boards.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(task_fields.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")