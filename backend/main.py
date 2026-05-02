from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import estudiantes, materias, calificaciones, carreras, recomendaciones, recomendaciones_automaticas

app = FastAPI(title="SIRA API", version="1.0.0", redirect_slashes=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(estudiantes.router, prefix="/api/estudiantes", tags=["Estudiantes"])
app.include_router(materias.router, prefix="/api/materias", tags=["Materias"])
app.include_router(calificaciones.router, prefix="/api/calificaciones", tags=["Calificaciones"])
app.include_router(carreras.router, prefix="/api/carreras", tags=["Carreras"])
app.include_router(recomendaciones.router, prefix="/api/recomendaciones", tags=["Recomendaciones"])
app.include_router(recomendaciones_automaticas.router, prefix="/api/recomendaciones-automaticas", tags=["Recomendaciones Automáticas"])

@app.get("/")
def root():
    return {"message": "SIRA API funcionando ✅"}
