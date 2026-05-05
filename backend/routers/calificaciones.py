from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from database import get_db

router = APIRouter()


class CalificacionCreate(BaseModel):
    estudiante_id: int
    materia_id: int
    parcial1: Optional[float] = None
    parcial2: Optional[float] = None
    nota_final: Optional[float] = None
    estado: Optional[str] = 'en_curso'
    semestre: Optional[int] = 1


class CalificacionUpdate(BaseModel):
    parcial1: Optional[float] = None
    parcial2: Optional[float] = None
    nota_final: Optional[float] = None
    estado: Optional[str] = None
    semestre: Optional[int] = None


def calcular_promedio(p1, p2, nota_final):
    """Si se provee nota_final la usa directamente, sino calcula promedio"""
    if nota_final is not None:
        return round(nota_final, 2)
    vals = [v for v in [p1, p2] if v is not None]
    return round(sum(vals) / len(vals), 2) if vals else 0.0


# GET todas las calificaciones (con filtro opcional)
@router.get("")
def listar_calificaciones(
    estudiante_id: Optional[int] = Query(None),
    materia_id: Optional[int] = Query(None),
    db=Depends(get_db)
):
    cursor = db.cursor(dictionary=True)
    try:
        query = """
            SELECT c.calificacion_id, c.estudiante_id, c.materia_id,
                   c.nota_parcial1, c.nota_parcial2, c.nota_final,
                   c.estado, c.semestre, c.creado_en,
                   e.nombre as estudiante_nombre, m.nombre as materia_nombre
            FROM sira.calificacion c
            JOIN sira.estudiante e ON c.estudiante_id = e.estudiante_id
            JOIN sira.materia m ON c.materia_id = m.materia_id
            WHERE 1=1
        """
        params = []
        if estudiante_id:
            query += " AND c.estudiante_id = %s"
            params.append(estudiante_id)
        if materia_id:
            query += " AND c.materia_id = %s"
            params.append(materia_id)
        query += " ORDER BY e.nombre, m.nombre"
        cursor.execute(query, params)
        result = cursor.fetchall()
        cursor.close()
        return result
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error al listar calificaciones: {str(e)}")


# GET calificaciones de un estudiante
@router.get("/estudiante/{estudiante_id}")
def calificaciones_por_estudiante(estudiante_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT c.calificacion_id, c.estudiante_id, c.materia_id,
                   c.nota_parcial1, c.nota_parcial2, c.nota_final,
                   c.estado, c.semestre, m.nombre as materia_nombre,
                   m.codigo, m.creditos
            FROM sira.calificacion c
            JOIN sira.materia m ON c.materia_id = m.materia_id
            WHERE c.estudiante_id = %s
            ORDER BY c.semestre, m.nombre
        """, (estudiante_id,))
        result = cursor.fetchall()
        cursor.close()
        return result
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=str(e))


# POST crear calificación
@router.post("", status_code=201)
def crear_calificacion(data: CalificacionCreate, db=Depends(get_db)):
    promedio = calcular_promedio(data.parcial1, data.parcial2, data.nota_final)
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            INSERT INTO sira.calificacion
                (estudiante_id, materia_id, nota_parcial1, nota_parcial2, nota_final, estado, semestre)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (data.estudiante_id, data.materia_id,
              data.parcial1, data.parcial2, promedio,
              data.estado or 'en_curso', data.semestre or 1))
        db.commit()
        id_creada = cursor.lastrowid
        cursor.execute("""
            SELECT c.*, e.nombre as estudiante_nombre, m.nombre as materia_nombre
            FROM sira.calificacion c
            JOIN sira.estudiante e ON c.estudiante_id = e.estudiante_id
            JOIN sira.materia m ON c.materia_id = m.materia_id
            WHERE c.calificacion_id = %s
        """, (id_creada,))
        calificacion = cursor.fetchone()
        cursor.close()
        return calificacion or {"calificacion_id": id_creada, "nota_final": promedio}
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=400, detail=str(e))


# PUT actualizar calificación
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
        fn = data.nota_final if data.nota_final is not None else actual["nota_final"]
        promedio = calcular_promedio(p1, p2, fn)
        estado = data.estado if data.estado else actual["estado"]
        semestre = data.semestre if data.semestre else actual["semestre"]

        cursor.execute("""
            UPDATE sira.calificacion
            SET nota_parcial1=%s, nota_parcial2=%s, nota_final=%s, estado=%s, semestre=%s
            WHERE calificacion_id=%s
        """, (p1, p2, promedio, estado, semestre, calificacion_id))
        db.commit()

        cursor.execute("""
            SELECT c.*, e.nombre as estudiante_nombre, m.nombre as materia_nombre
            FROM sira.calificacion c
            JOIN sira.estudiante e ON c.estudiante_id = e.estudiante_id
            JOIN sira.materia m ON c.materia_id = m.materia_id
            WHERE c.calificacion_id = %s
        """, (calificacion_id,))
        calificacion = cursor.fetchone()
        cursor.close()
        return calificacion or {"message": "Actualizada", "nota_final": promedio}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=400, detail=str(e))


# DELETE calificación
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