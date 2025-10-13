# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import tasks, workflow, roles, users, auth, boards, task_fields, analytics
from app.core.database import Base, engine

app = FastAPI(title="SGT_v1 - Backend")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://sgt-frontend-production.s3-website.us-east-2.amazonaws.com",  # S3 Production
        "https://*.cloudfront.net",  # CloudFront (futuro)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Crear tablas si no existen
Base.metadata.create_all(bind=engine)

# Routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(workflow.router, prefix="/api/v1")
app.include_router(roles.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(boards.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(task_fields.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")