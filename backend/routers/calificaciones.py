from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, field_validator
from typing import Optional
from database import get_db

router = APIRouter()

class CalificacionCreate(BaseModel):
    estudiante_id: int
    materia_id: int
    num_parciales: Optional[int] = 2       # cuántos parciales tiene la materia
    parcial1: Optional[float] = None
    parcial2: Optional[float] = None
    parcial3: Optional[float] = None
    nota_final: Optional[float] = None
    estado: Optional[str] = 'en_curso'
    semestre: Optional[int] = 1
    observaciones: Optional[str] = None

    @field_validator('parcial1', 'parcial2', 'parcial3', 'nota_final', mode='before')
    @classmethod
    def validar_rango(cls, v):
        if v is not None and not (0 <= float(v) <= 10):
            raise ValueError('La nota debe estar entre 0 y 10')
        return v


class CalificacionUpdate(BaseModel):
    num_parciales: Optional[int] = None
    parcial1: Optional[float] = None
    parcial2: Optional[float] = None
    parcial3: Optional[float] = None
    nota_final: Optional[float] = None
    estado: Optional[str] = None
    semestre: Optional[int] = None
    observaciones: Optional[str] = None

    @field_validator('parcial1', 'parcial2', 'parcial3', 'nota_final', mode='before')
    @classmethod
    def validar_rango(cls, v):
        if v is not None and not (0 <= float(v) <= 10):
            raise ValueError('La nota debe estar entre 0 y 10')
        return v


def calcular_promedio(parciales: list, nota_final=None):
    """Si se provee nota_final la usa directamente, sino calcula promedio de parciales"""
    if nota_final is not None:
        return round(float(nota_final), 2)
    vals = [v for v in parciales if v is not None]
    return round(sum(vals) / len(vals), 2) if vals else 0.0


def auto_estado(nota_final: float) -> str:
    """Determina estado automáticamente si nota_final está completa"""
    if nota_final >= 6.0:
        return 'aprobado'
    return 'reprobado'


# ── GET todas las calificaciones ─────────────────────────────────────────────
@router.get("")
def listar_calificaciones(
    estudiante_id: Optional[int] = Query(None),
    materia_id: Optional[int] = Query(None),
    db=Depends(get_db)
):
    cursor = db.cursor(dictionary=True)

    def _build_query(extended: bool) -> str:
        cols = """c.calificacion_id, c.estudiante_id, c.materia_id,
                   c.nota_parcial1, c.nota_parcial2, c.nota_final,
                   c.estado, c.semestre, c.creado_en,
                   e.nombre as estudiante_nombre, m.nombre as materia_nombre"""
        if extended:
            cols += ", c.nota_parcial3, c.observaciones, c.num_parciales"
        return f"""
            SELECT {cols}
            FROM sira.calificacion c
            JOIN sira.estudiante e ON c.estudiante_id = e.estudiante_id
            JOIN sira.materia m ON c.materia_id = m.materia_id
            WHERE 1=1
        """

    try:
        params = []
        filters = ""
        if estudiante_id:
            filters += " AND c.estudiante_id = %s"
            params.append(estudiante_id)
        if materia_id:
            filters += " AND c.materia_id = %s"
            params.append(materia_id)
        order = " ORDER BY e.nombre, m.nombre"

        try:
            cursor.execute(_build_query(extended=True) + filters + order, params)
        except Exception:
            db.rollback()
            cursor.execute(_build_query(extended=False) + filters + order, params)

        result = cursor.fetchall()
        cursor.close()
        return result
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ── GET calificaciones de un estudiante ──────────────────────────────────────
@router.get("/estudiante/{estudiante_id}")
def calificaciones_por_estudiante(estudiante_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        try:
            cursor.execute("""
                SELECT c.calificacion_id, c.estudiante_id, c.materia_id,
                       c.nota_parcial1, c.nota_parcial2, c.nota_parcial3,
                       c.nota_final, c.estado, c.semestre, c.observaciones,
                       c.num_parciales, m.nombre as materia_nombre,
                       m.codigo, m.creditos
                FROM sira.calificacion c
                JOIN sira.materia m ON c.materia_id = m.materia_id
                WHERE c.estudiante_id = %s
                ORDER BY c.semestre, m.nombre
            """, (estudiante_id,))
        except Exception:
            db.rollback()
            cursor.execute("""
                SELECT c.calificacion_id, c.estudiante_id, c.materia_id,
                       c.nota_parcial1, c.nota_parcial2,
                       c.nota_final, c.estado, c.semestre,
                       m.nombre as materia_nombre, m.codigo, m.creditos
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


# ── POST crear calificación ───────────────────────────────────────────────────
@router.post("", status_code=201)
def crear_calificacion(data: CalificacionCreate, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        # Verificar que el estudiante existe
        cursor.execute(
            "SELECT estudiante_id FROM sira.estudiante WHERE estudiante_id = %s",
            (data.estudiante_id,)
        )
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")

        # Verificar que la materia existe
        cursor.execute(
            "SELECT materia_id FROM sira.materia WHERE materia_id = %s",
            (data.materia_id,)
        )
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Materia no encontrada")

        # Calcular promedio según parciales disponibles
        parciales = [data.parcial1, data.parcial2, data.parcial3]
        promedio = calcular_promedio(parciales, data.nota_final)

        # Auto-estado si nota_final está definida y estado no es en_curso
        estado = data.estado or 'en_curso'
        if promedio > 0 and estado == 'en_curso' and data.nota_final is not None:
            estado = auto_estado(promedio)

        semestre = data.semestre or 1

        # ── Buscar o crear inscripcion_id (requerido por FK de la tabla) ──────
        inscripcion_id = None
        cursor.execute("""
            SELECT inscripcion_id FROM sira.inscripcion
            WHERE estudiante_id = %s AND materia_id = %s AND semestre_cursado = %s
            LIMIT 1
        """, (data.estudiante_id, data.materia_id, semestre))
        row = cursor.fetchone()
        if row:
            inscripcion_id = row['inscripcion_id']
        else:
            cursor.execute("""
                INSERT INTO sira.inscripcion
                    (estudiante_id, materia_id, semestre_cursado, estado)
                VALUES (%s, %s, %s, 'activa')
            """, (data.estudiante_id, data.materia_id, semestre))
            inscripcion_id = cursor.lastrowid

        # ── Verificar que no exista ya una calificación para esa inscripción ──
        cursor.execute(
            "SELECT calificacion_id FROM sira.calificacion WHERE inscripcion_id = %s",
            (inscripcion_id,)
        )
        if cursor.fetchone():
            raise HTTPException(
                status_code=400,
                detail="Ya existe una calificación para este estudiante y materia en ese semestre"
            )

        # ── INSERT con columnas opcionales y fallback ─────────────────────────
        try:
            cursor.execute("""
                INSERT INTO sira.calificacion
                    (inscripcion_id, estudiante_id, materia_id,
                     nota_parcial1, nota_parcial2, nota_parcial3,
                     nota_final, estado, semestre,
                     observaciones, num_parciales)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                inscripcion_id,
                data.estudiante_id, data.materia_id,
                data.parcial1, data.parcial2, data.parcial3,
                promedio, estado, semestre,
                data.observaciones, data.num_parciales or 2
            ))
        except Exception:
            cursor.execute("""
                INSERT INTO sira.calificacion
                    (inscripcion_id, estudiante_id, materia_id,
                     nota_parcial1, nota_parcial2,
                     nota_final, estado, semestre)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                inscripcion_id,
                data.estudiante_id, data.materia_id,
                data.parcial1, data.parcial2,
                promedio, estado, semestre
            ))

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

    except HTTPException:
        cursor.close()
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=400, detail=str(e))


# ── PUT actualizar calificación ───────────────────────────────────────────────
@router.put("/{calificacion_id}")
def actualizar_calificacion(calificacion_id: int, data: CalificacionUpdate, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT * FROM sira.calificacion WHERE calificacion_id = %s",
            (calificacion_id,)
        )
        actual = cursor.fetchone()
        if not actual:
            cursor.close()
            raise HTTPException(status_code=404, detail="Calificación no encontrada")

        p1 = data.parcial1 if data.parcial1 is not None else actual.get("nota_parcial1")
        p2 = data.parcial2 if data.parcial2 is not None else actual.get("nota_parcial2")
        p3 = data.parcial3 if data.parcial3 is not None else actual.get("nota_parcial3")
        fn = data.nota_final if data.nota_final is not None else actual.get("nota_final")
        promedio = calcular_promedio([p1, p2, p3], fn)

        estado = data.estado if data.estado else actual.get("estado", "en_curso")
        if promedio > 0 and estado == 'en_curso' and fn is not None:
            estado = auto_estado(promedio)

        semestre = data.semestre if data.semestre else actual.get("semestre", 1)
        observaciones = data.observaciones if data.observaciones is not None else actual.get("observaciones")
        num_parciales = data.num_parciales if data.num_parciales else actual.get("num_parciales", 2)

        try:
            cursor.execute("""
                UPDATE sira.calificacion
                SET nota_parcial1=%s, nota_parcial2=%s, nota_parcial3=%s,
                    nota_final=%s, estado=%s, semestre=%s,
                    observaciones=%s, num_parciales=%s
                WHERE calificacion_id=%s
            """, (p1, p2, p3, promedio, estado, semestre,
                  observaciones, num_parciales, calificacion_id))
        except Exception:
            cursor.execute("""
                UPDATE sira.calificacion
                SET nota_parcial1=%s, nota_parcial2=%s, nota_final=%s,
                    estado=%s, semestre=%s
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


# ── DELETE calificación ───────────────────────────────────────────────────────
@router.delete("/{calificacion_id}")
def eliminar_calificacion(calificacion_id: int, db=Depends(get_db)):
    cursor = db.cursor()
    try:
        cursor.execute(
            "DELETE FROM sira.calificacion WHERE calificacion_id = %s",
            (calificacion_id,)
        )
        db.commit()
        cursor.close()
        return {"message": "Calificación eliminada"}
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=400, detail=str(e))