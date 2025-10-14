# app/api/task_fields.py
from fastapi import APIRouter, HTTPException, Depends, status
from app.api.auth import get_current_user
from app.models.user import User
import json
import os
from pathlib import Path
from typing import Dict, Any

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

def save_task_config(config: Dict[str, Any]):
    """Guardar la configuración de campos de tareas al JSON"""
    try:
        # Crear backup antes de sobrescribir
        backup_file = CONFIG_FILE.with_suffix('.json.backup')
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                backup_content = f.read()
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(backup_content)
        
        # Guardar nueva configuración
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error saving configuration: {str(e)}"
        )

@router.get("/")
def get_all_task_configs(current_user: User = Depends(get_current_user)):
    """
    Obtener todas las configuraciones de campos
    
    Requiere autenticación
    """
    return load_task_config()

@router.get("/{workflow_name}")
def get_task_config_by_workflow(
    workflow_name: str,
    current_user: User = Depends(get_current_user)
):
    """
    Obtener configuración de campos para un workflow específico
    
    Requiere autenticación
    """
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

@router.put("/")
def update_task_config(
    config: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """
    Actualizar la configuración completa de campos de tareas
    
    Solo Administrador y Manager pueden actualizar
    """
    # Verificar permisos
    role_name = current_user.role.name if current_user.role else None
    
    if role_name not in ["Administrador", "Manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Solo Administrador y Manager pueden editar la configuración. Tu rol: {role_name}"
        )
    
    print(f"✅ Usuario {current_user.username} ({role_name}) actualizando configuración de campos")
    
    # Validar estructura básica
    if not isinstance(config, dict):
        raise HTTPException(
            status_code=400,
            detail="La configuración debe ser un objeto JSON"
        )
    
    # Validar que cada workflow tenga la estructura correcta
    for workflow_name, fields in config.items():
        if not isinstance(fields, dict):
            raise HTTPException(
                status_code=400,
                detail=f"Los campos del workflow '{workflow_name}' deben ser un objeto"
            )
        
        for field_key, field_config in fields.items():
            if not isinstance(field_config, dict):
                raise HTTPException(
                    status_code=400,
                    detail=f"La configuración del campo '{field_key}' en '{workflow_name}' debe ser un objeto"
                )
            
            # Validar campos requeridos
            required_keys = ["name", "type", "val"]
            for key in required_keys:
                if key not in field_config:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Falta el campo '{key}' en '{field_key}' del workflow '{workflow_name}'"
                    )
            
            # Validar tipo
            valid_types = ["input", "select", "multiselect"]
            if field_config["type"] not in valid_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"Tipo inválido '{field_config['type']}' en campo '{field_key}'. Tipos válidos: {valid_types}"
                )
            
            # Validar val según el tipo
            if field_config["type"] in ["select", "multiselect"]:
                if not isinstance(field_config["val"], list):
                    raise HTTPException(
                        status_code=400,
                        detail=f"El campo 'val' de '{field_key}' debe ser una lista para tipo {field_config['type']}"
                    )
            elif field_config["type"] == "input":
                valid_input_types = ["txt", "num", "txtnum", "none"]
                if field_config["val"] not in valid_input_types:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Valor inválido '{field_config['val']}' en campo '{field_key}'. Valores válidos para input: {valid_input_types}"
                    )
    
    # Guardar configuración
    save_task_config(config)
    
    print(f"✅ Configuración de campos actualizada exitosamente por {current_user.username}")
    
    return {
        "message": "Configuración actualizada exitosamente",
        "updated_by": current_user.username
    }

@router.post("/restore-backup")
def restore_backup(current_user: User = Depends(get_current_user)):
    """
    Restaurar configuración desde el backup
    
    Solo Administrador puede restaurar
    """
    # Verificar permisos
    role_name = current_user.role.name if current_user.role else None
    
    if role_name != "Administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo Administrador puede restaurar el backup"
        )
    
    backup_file = CONFIG_FILE.with_suffix('.json.backup')
    
    if not backup_file.exists():
        raise HTTPException(
            status_code=404,
            detail="No se encontró archivo de backup"
        )
    
    try:
        # Leer backup
        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_config = json.load(f)
        
        # Restaurar
        save_task_config(backup_config)
        
        print(f"✅ Configuración restaurada desde backup por {current_user.username}")
        
        return {
            "message": "Configuración restaurada exitosamente desde backup",
            "restored_by": current_user.username
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error restaurando backup: {str(e)}"
        )