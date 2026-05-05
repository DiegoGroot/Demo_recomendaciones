from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from database import get_db
from mysql.connector import errors as mysql_errors

router = APIRouter()


class InscripcionCreate(BaseModel):
    estudiante_id: int
    materia_id: int
    semestre_cursado: int = 1
    anio_academico: Optional[int] = None
    periodo: Optional[str] = None


class InscripcionUpdate(BaseModel):
    estado: Optional[str] = None
    semestre_cursado: Optional[int] = None


# GET todas las inscripciones (con filtros opcionales)
@router.get("")
def listar_inscripciones(
    estudiante_id: Optional[int] = Query(None),
    materia_id: Optional[int] = Query(None),
    estado: Optional[str] = Query(None),
    db=Depends(get_db),
):
    cursor = db.cursor(dictionary=True)
    try:
        query = """
            SELECT i.inscripcion_id, i.estudiante_id, i.materia_id,
                   i.semestre_cursado, i.anio_academico, i.periodo,
                   i.estado, i.fecha_inscripcion,
                   e.nombre as estudiante_nombre,
                   m.nombre as materia_nombre,
                   c.nombre as calificacion_id
            FROM sira.inscripcion i
            JOIN sira.estudiante e ON i.estudiante_id = e.estudiante_id
            JOIN sira.materia m ON i.materia_id = m.materia_id
            LEFT JOIN sira.calificacion c ON i.inscripcion_id = c.inscripcion_id
            WHERE 1=1
        """
        params = []
        
        if estudiante_id:
            query += " AND i.estudiante_id = %s"
            params.append(estudiante_id)
        
        if materia_id:
            query += " AND i.materia_id = %s"
            params.append(materia_id)
        
        if estado:
            query += " AND i.estado = %s"
            params.append(estado)
        
        query += " ORDER BY e.nombre, m.nombre"
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        result = cursor.fetchall()
        cursor.close()
        return result
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error al listar inscripciones: {str(e)}")


# GET inscripciones de un estudiante
@router.get("/estudiante/{estudiante_id}")
def inscripciones_por_estudiante(estudiante_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT i.inscripcion_id, i.estudiante_id, i.materia_id,
                   i.semestre_cursado, i.anio_academico, i.periodo,
                   i.estado, i.fecha_inscripcion,
                   m.nombre as materia_nombre, m.codigo, m.creditos, m.semestre,
                   c.nombre as carrera_nombre
            FROM sira.inscripcion i
            JOIN sira.materia m ON i.materia_id = m.materia_id
            LEFT JOIN sira.carrera c ON m.carrera_id = c.carrera_id
            WHERE i.estudiante_id = %s
            ORDER BY m.semestre, m.nombre
        """, (estudiante_id,))
        result = cursor.fetchall()
        cursor.close()
        return result if result else []
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# GET inscripciones de una materia
@router.get("/materia/{materia_id}")
def inscripciones_por_materia(materia_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT i.inscripcion_id, i.estudiante_id, i.materia_id,
                   i.semestre_cursado, i.anio_academico, i.periodo,
                   i.estado, i.fecha_inscripcion,
                   e.nombre as estudiante_nombre, e.correo,
                   cal.calificacion_id, cal.nota_parcial1, cal.nota_parcial2, cal.nota_final
            FROM sira.inscripcion i
            JOIN sira.estudiante e ON i.estudiante_id = e.estudiante_id
            LEFT JOIN sira.calificacion cal ON i.inscripcion_id = cal.inscripcion_id
            WHERE i.materia_id = %s
            ORDER BY e.nombre
        """, (materia_id,))
        result = cursor.fetchall()
        cursor.close()
        return result if result else []
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# GET una inscripción específica
@router.get("/{inscripcion_id}")
def obtener_inscripcion(inscripcion_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT i.inscripcion_id, i.estudiante_id, i.materia_id,
                   i.semestre_cursado, i.anio_academico, i.periodo,
                   i.estado, i.fecha_inscripcion,
                   e.nombre as estudiante_nombre,
                   m.nombre as materia_nombre
            FROM sira.inscripcion i
            JOIN sira.estudiante e ON i.estudiante_id = e.estudiante_id
            JOIN sira.materia m ON i.materia_id = m.materia_id
            WHERE i.inscripcion_id = %s
        """, (inscripcion_id,))
        row = cursor.fetchone()
        cursor.close()
        if not row:
            raise HTTPException(status_code=404, detail="Inscripción no encontrada")
        return row
    except HTTPException:
        raise
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# POST crear inscripción
@router.post("", status_code=201)
def crear_inscripcion(data: InscripcionCreate, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        # Verificar que el estudiante existe
        cursor.execute("SELECT estudiante_id FROM sira.estudiante WHERE estudiante_id = %s", (data.estudiante_id,))
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")
        
        # Verificar que la materia existe
        cursor.execute("SELECT materia_id FROM sira.materia WHERE materia_id = %s", (data.materia_id,))
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Materia no encontrada")
        
        # Verificar si ya existe inscripción
        cursor.execute("""
            SELECT inscripcion_id FROM sira.inscripcion
            WHERE estudiante_id = %s AND materia_id = %s AND semestre_cursado = %s AND anio_academico = %s
        """, (data.estudiante_id, data.materia_id, data.semestre_cursado, data.anio_academico))
        if cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=409, detail="Esta inscripción ya existe")
        
        cursor.execute("""
            INSERT INTO sira.inscripcion (estudiante_id, materia_id, semestre_cursado, anio_academico, periodo)
            VALUES (%s, %s, %s, %s, %s)
        """, (data.estudiante_id, data.materia_id, data.semestre_cursado, data.anio_academico, data.periodo))
        db.commit()
        new_id = cursor.lastrowid
        
        cursor.execute("""
            SELECT i.inscripcion_id, i.estudiante_id, i.materia_id,
                   i.semestre_cursado, i.anio_academico, i.periodo,
                   i.estado, i.fecha_inscripcion,
                   e.nombre as estudiante_nombre,
                   m.nombre as materia_nombre
            FROM sira.inscripcion i
            JOIN sira.estudiante e ON i.estudiante_id = e.estudiante_id
            JOIN sira.materia m ON i.materia_id = m.materia_id
            WHERE i.inscripcion_id = %s
        """, (new_id,))
        inscripcion = cursor.fetchone()
        cursor.close()
        return inscripcion
    except HTTPException:
        cursor.close()
        raise
    except mysql_errors.IntegrityError as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=409, detail="Error de integridad: inscripción duplicada")
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# PUT actualizar inscripción
@router.put("/{inscripcion_id}")
def actualizar_inscripcion(inscripcion_id: int, data: InscripcionUpdate, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT inscripcion_id FROM sira.inscripcion WHERE inscripcion_id = %s", (inscripcion_id,))
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Inscripción no encontrada")
        
        campos = {k: v for k, v in data.dict().items() if v is not None}
        if not campos:
            cursor.close()
            raise HTTPException(status_code=400, detail="Sin datos para actualizar")
        
        set_clause = ", ".join([f"{k} = %s" for k in campos])
        cursor.execute(
            f"UPDATE sira.inscripcion SET {set_clause} WHERE inscripcion_id = %s",
            (*campos.values(), inscripcion_id)
        )
        db.commit()
        
        cursor.execute("""
            SELECT i.inscripcion_id, i.estudiante_id, i.materia_id,
                   i.semestre_cursado, i.anio_academico, i.periodo,
                   i.estado, i.fecha_inscripcion,
                   e.nombre as estudiante_nombre,
                   m.nombre as materia_nombre
            FROM sira.inscripcion i
            JOIN sira.estudiante e ON i.estudiante_id = e.estudiante_id
            JOIN sira.materia m ON i.materia_id = m.materia_id
            WHERE i.inscripcion_id = %s
        """, (inscripcion_id,))
        inscripcion = cursor.fetchone()
        cursor.close()
        return inscripcion
    except HTTPException:
        cursor.close()
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# DELETE inscripción
@router.delete("/{inscripcion_id}")
def eliminar_inscripcion(inscripcion_id: int, db=Depends(get_db)):
    cursor = db.cursor()
    try:
        cursor.execute("SELECT inscripcion_id FROM sira.inscripcion WHERE inscripcion_id = %s", (inscripcion_id,))
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Inscripción no encontrada")
        
        cursor.execute("DELETE FROM sira.inscripcion WHERE inscripcion_id = %s", (inscripcion_id,))
        db.commit()
        cursor.close()
        return {"message": "Inscripción eliminada"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
