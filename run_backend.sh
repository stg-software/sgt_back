#!/bin/bash
# Cargar variables del archivo .env
export $(grep -v '^#' .env | xargs)

source sgtEnv/Scripts/activate

# Iniciar uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
