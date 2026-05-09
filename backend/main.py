from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import (
    estudiantes, materias, calificaciones,
    carreras, recomendaciones, auth, inscripcion, evaluaciones)

app = FastAPI(title="SIRA API", version="2.0.0", redirect_slashes=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AUTH primero - debe ir ANTES que los routers de recursos
# para evitar que /api/maestros/{id} intercepte /api/auth/maestros/login
app.include_router(auth.router, prefix="/api/auth", tags=["Autenticación"])

# Endpoints de recursos principales
app.include_router(estudiantes.router,     prefix="/api/estudiantes",    tags=["Estudiantes"])
app.include_router(materias.router,        prefix="/api/materias",       tags=["Materias"])
app.include_router(calificaciones.router,  prefix="/api/calificaciones", tags=["Calificaciones"])
app.include_router(inscripcion.router,     prefix="/api/inscripciones",  tags=["Inscripciones"])
app.include_router(carreras.router,        prefix="/api/carreras",       tags=["Carreras"])
app.include_router(recomendaciones.router, prefix="/api/recomendaciones",tags=["Recomendaciones"])
app.include_router(evaluaciones.router,    prefix="/api/evaluaciones",   tags=["Evaluaciones"])

@app.get("/")
def root():
    return {
        "message": "SIRA API v2.0 ✅",
        "version": "2.0.0",
        "status": "running"
    }

@app.get("/api/health")
def health():
    return {"status": "healthy"}