# app/api/task_fields.py
from fastapi import APIRouter, HTTPException
import json
import os
from pathlib import Path

router = APIRouter(prefix="/task-fields", tags=["Task Fields"])

# Ruta al archivo de configuración
CONFIG_FILE = Path(__file__).parent.parent / "config" / "taskConfig.json"

def load_task_config():
    """Cargar la configuración de campos de tareas desde el JSON"""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Task configuration file not found")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid task configuration file")

@router.get("/")
def get_all_task_configs():
    """Obtener todas las configuraciones de campos"""
    return load_task_config()

@router.get("/{workflow_name}")
def get_task_config_by_workflow(workflow_name: str):
    """Obtener configuración de campos para un workflow específico"""
    config = load_task_config()
    
    if workflow_name not in config:
        raise HTTPException(
            status_code=404, 
            detail=f"Configuration for workflow '{workflow_name}' not found"
        )
    
    return {
        "workflow_name": workflow_name,
        "fields": config[workflow_name]
    }