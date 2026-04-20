from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import get_db

router = APIRouter()

class CalificacionCreate(BaseModel):
    inscripcion_id: int
    parcial1: float
    parcial2: float
    parcial3: float

class CalificacionUpdate(BaseModel):
    parcial1: Optional[float] = None
    parcial2: Optional[float] = None
    parcial3: Optional[float] = None

def calcular_promedio(p1, p2, p3):
    vals = [v for v in [p1, p2, p3] if v is not None]
    return round(sum(vals) / len(vals), 2) if vals else 0

@router.get("/")
def listar_calificaciones(db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT c.*, e.nombre as estudiante, m.nombre as materia
            FROM sira.calificacion c
            JOIN sira.estudiante e ON c.estudiante_id = e.estudiante_id
            JOIN sira.materia m ON c.materia_id = m.materia_id
        """)
        result = cursor.fetchall()
        cursor.close()
        return result
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error al listar calificaciones: {str(e)}")

@router.get("/estudiante/{estudiante_id}")
def calificaciones_por_estudiante(estudiante_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT c.*, m.nombre as materia
            FROM sira.calificacion c
            JOIN sira.materia m ON c.materia_id = m.materia_id
            WHERE c.estudiante_id = %s
        """, (estudiante_id,))
        result = cursor.fetchall()
        cursor.close()
        return result
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error al listar calificaciones: {str(e)}")

@router.post("/", status_code=201)
def crear_calificacion(data: CalificacionCreate, db=Depends(get_db)):
    promedio = calcular_promedio(data.parcial1, data.parcial2, data.parcial3)
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            INSERT INTO sira.calificacion (estudiante_id, materia_id, nota_parcial1, nota_parcial2, nota_final)
            VALUES (%s, %s, %s, %s, %s)
        """, (data.inscripcion_id, data.parcial1, data.parcial2, data.parcial3, promedio))
        db.commit()
        id_creada = cursor.lastrowid
        cursor.execute("""
            SELECT c.*, e.nombre as estudiante, m.nombre as materia
            FROM sira.calificacion c
            JOIN sira.estudiante e ON c.estudiante_id = e.estudiante_id
            JOIN sira.materia m ON c.materia_id = m.materia_id
            WHERE c.calificacion_id = %s
        """, (id_creada,))
        calificacion = cursor.fetchone()
        cursor.close()
        return calificacion if calificacion else {"calificacion_id": id_creada, "promedio": promedio}
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{calificacion_id}")
def actualizar_calificacion(calificacion_id: int, data: CalificacionUpdate, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM sira.calificacion WHERE calificacion_id = %s", (calificacion_id,))
        actual = cursor.fetchone()
        if not actual:
            cursor.close()
            raise HTTPException(status_code=404, detail="Calificación no encontrada")
        p1 = data.parcial1 if data.parcial1 is not None else actual["nota_parcial1"]
        p2 = data.parcial2 if data.parcial2 is not None else actual["nota_parcial2"]
        p3 = data.parcial3 if data.parcial3 is not None else 0
        promedio = calcular_promedio(p1, p2, p3)
        cursor.execute("""
            UPDATE sira.calificacion
            SET nota_parcial1=%s, nota_parcial2=%s, nota_final=%s
            WHERE calificacion_id=%s
        """, (p1, p2, promedio, calificacion_id))
        db.commit()
        cursor.execute("""
            SELECT c.*, e.nombre as estudiante, m.nombre as materia
            FROM sira.calificacion c
            JOIN sira.estudiante e ON c.estudiante_id = e.estudiante_id
            JOIN sira.materia m ON c.materia_id = m.materia_id
            WHERE c.calificacion_id = %s
        """, (calificacion_id,))
        calificacion = cursor.fetchone()
        cursor.close()
        return calificacion if calificacion else {"message": "Calificación actualizada", "promedio": promedio}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{calificacion_id}")
def eliminar_calificacion(calificacion_id: int, db=Depends(get_db)):
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM sira.calificacion WHERE calificacion_id = %s", (calificacion_id,))
        db.commit()
        cursor.close()
        return {"message": "Calificación eliminada"}
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=400, detail=str(e))
