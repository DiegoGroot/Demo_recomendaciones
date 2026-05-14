from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, field_validator
from typing import Optional
from database import get_db

router = APIRouter()


class CalificacionCreate(BaseModel):
    estudiante_id: int
    materia_id: int
    num_parciales: Optional[int] = 2
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
    if nota_final is not None:
        return round(float(nota_final), 2)
    vals = [v for v in parciales if v is not None]
    return round(sum(vals) / len(vals), 2) if vals else None  # None en vez de 0 para evitar constraint


def auto_estado(nota_final: float) -> str:
    if nota_final >= 6.0:
        return 'aprobado'
    return 'reprobado'


def _columnas_tabla(cursor, tabla: str) -> set:
    cursor.execute("""
        SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s
    """, (tabla,))
    return {row['COLUMN_NAME'] for row in cursor.fetchall()}


# ── GET todas las calificaciones ─────────────────────────────────────────────
@router.get("")
def listar_calificaciones(
    estudiante_id: Optional[int] = Query(None),
    materia_id: Optional[int] = Query(None),
    db=Depends(get_db)
):
    cursor = db.cursor(dictionary=True)
    try:
        cols = _columnas_tabla(cursor, 'calificacion')
        extra = ""
        if 'nota_parcial3' in cols:
            extra += ", c.nota_parcial3"
        if 'observaciones' in cols:
            extra += ", c.observaciones"
        if 'num_parciales' in cols:
            extra += ", c.num_parciales"

        query = f"""
            SELECT c.calificacion_id, c.estudiante_id, c.materia_id,
                   c.nota_parcial1, c.nota_parcial2, c.nota_final,
                   c.estado, c.semestre, c.creado_en,
                   e.nombre as estudiante_nombre, m.nombre as materia_nombre
                   {extra}
            FROM calificacion c
            JOIN estudiante e ON c.estudiante_id = e.estudiante_id
            JOIN materia m ON c.materia_id = m.materia_id
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
        return result if result else []
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ── GET calificaciones de un estudiante ──────────────────────────────────────
@router.get("/estudiante/{estudiante_id}")
def calificaciones_por_estudiante(estudiante_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cols = _columnas_tabla(cursor, 'calificacion')
        extra = ""
        if 'nota_parcial3' in cols:
            extra += ", c.nota_parcial3"
        if 'observaciones' in cols:
            extra += ", c.observaciones"
        if 'num_parciales' in cols:
            extra += ", c.num_parciales"

        cursor.execute(f"""
            SELECT c.calificacion_id, c.estudiante_id, c.materia_id,
                   c.nota_parcial1, c.nota_parcial2,
                   c.nota_final, c.estado, c.semestre,
                   m.nombre as materia_nombre, m.codigo, m.creditos
                   {extra}
            FROM calificacion c
            JOIN materia m ON c.materia_id = m.materia_id
            WHERE c.estudiante_id = %s
            ORDER BY c.semestre, m.nombre
        """, (estudiante_id,))
        result = cursor.fetchall()
        cursor.close()
        return result if result else []
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=str(e))


# ── POST crear calificación ───────────────────────────────────────────────────
@router.post("", status_code=201)
def crear_calificacion(data: CalificacionCreate, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT estudiante_id FROM estudiante WHERE estudiante_id = %s", (data.estudiante_id,))
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")

        cursor.execute("SELECT materia_id FROM materia WHERE materia_id = %s", (data.materia_id,))
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Materia no encontrada")

        parciales = [data.parcial1, data.parcial2, data.parcial3]
        promedio = calcular_promedio(parciales, data.nota_final)

        estado = data.estado or 'en_curso'
        if promedio is not None and promedio > 0 and estado == 'en_curso' and data.nota_final is not None:
            estado = auto_estado(promedio)

        semestre = data.semestre or 1

        # Buscar o crear inscripcion_id
        cols_insc = _columnas_tabla(cursor, 'inscripcion')
        inscripcion_id = None

        if 'semestre_cursado' in cols_insc:
            cursor.execute("""
                SELECT inscripcion_id FROM inscripcion
                WHERE estudiante_id = %s AND materia_id = %s AND semestre_cursado = %s
                LIMIT 1
            """, (data.estudiante_id, data.materia_id, semestre))
        else:
            cursor.execute("""
                SELECT inscripcion_id FROM inscripcion
                WHERE estudiante_id = %s AND materia_id = %s
                LIMIT 1
            """, (data.estudiante_id, data.materia_id))

        row = cursor.fetchone()
        if row:
            inscripcion_id = row['inscripcion_id']
        else:
            if 'semestre_cursado' in cols_insc and 'estado' in cols_insc:
                cursor.execute("""
                    INSERT INTO inscripcion (estudiante_id, materia_id, semestre_cursado, estado)
                    VALUES (%s, %s, %s, 'activa')
                """, (data.estudiante_id, data.materia_id, semestre))
            else:
                cursor.execute("""
                    INSERT INTO inscripcion (estudiante_id, materia_id)
                    VALUES (%s, %s)
                """, (data.estudiante_id, data.materia_id))
            inscripcion_id = cursor.lastrowid

        # Verificar que no exista ya una calificación
        cursor.execute(
            "SELECT calificacion_id FROM calificacion WHERE inscripcion_id = %s",
            (inscripcion_id,)
        )
        if cursor.fetchone():
            cursor.close()
            raise HTTPException(
                status_code=400,
                detail="Ya existe una calificación para este estudiante y materia en ese semestre"
            )

        # INSERT con columnas reales
        cols_cal = _columnas_tabla(cursor, 'calificacion')

        campos = {
            'inscripcion_id': inscripcion_id,
            'estudiante_id': data.estudiante_id,
            'materia_id': data.materia_id,
            'nota_parcial1': data.parcial1,
            'nota_parcial2': data.parcial2,
            'estado': estado,
            'semestre': semestre,
        }
        # Solo incluir nota_final si hay un promedio válido (evita constraint chk_estudiante_promedio)
        if promedio is not None:
            campos['nota_final'] = promedio
        if 'nota_parcial3' in cols_cal:
            campos['nota_parcial3'] = data.parcial3
        if 'observaciones' in cols_cal:
            campos['observaciones'] = data.observaciones
        if 'num_parciales' in cols_cal:
            campos['num_parciales'] = data.num_parciales or 2

        col_names = ", ".join(campos.keys())
        placeholders = ", ".join(["%s"] * len(campos))
        cursor.execute(
            f"INSERT INTO calificacion ({col_names}) VALUES ({placeholders})",
            list(campos.values())
        )
        db.commit()
        id_creada = cursor.lastrowid

        cursor.execute("""
            SELECT c.*, e.nombre as estudiante_nombre, m.nombre as materia_nombre
            FROM calificacion c
            JOIN estudiante e ON c.estudiante_id = e.estudiante_id
            JOIN materia m ON c.materia_id = m.materia_id
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
        cursor.execute("SELECT * FROM calificacion WHERE calificacion_id = %s", (calificacion_id,))
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
        if promedio is not None and promedio > 0 and estado == 'en_curso' and fn is not None:
            estado = auto_estado(promedio)

        semestre = data.semestre if data.semestre else actual.get("semestre", 1)
        observaciones = data.observaciones if data.observaciones is not None else actual.get("observaciones")
        num_parciales = data.num_parciales if data.num_parciales else actual.get("num_parciales", 2)

        cols_cal = _columnas_tabla(cursor, 'calificacion')

        campos = {
            'nota_parcial1': p1,
            'nota_parcial2': p2,
            'nota_final': promedio,
            'estado': estado,
            'semestre': semestre,
        }
        if 'nota_parcial3' in cols_cal:
            campos['nota_parcial3'] = p3
        if 'observaciones' in cols_cal:
            campos['observaciones'] = observaciones
        if 'num_parciales' in cols_cal:
            campos['num_parciales'] = num_parciales

        set_parts = ", ".join([f"{k}=%s" for k in campos])
        valores = list(campos.values())
        valores.append(calificacion_id)

        cursor.execute(
            f"UPDATE calificacion SET {set_parts} WHERE calificacion_id=%s",
            tuple(valores)
        )
        db.commit()

        cursor.execute("""
            SELECT c.*, e.nombre as estudiante_nombre, m.nombre as materia_nombre
            FROM calificacion c
            JOIN estudiante e ON c.estudiante_id = e.estudiante_id
            JOIN materia m ON c.materia_id = m.materia_id
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
        cursor.execute("DELETE FROM calificacion WHERE calificacion_id = %s", (calificacion_id,))
        db.commit()
        cursor.close()
        return {"message": "Calificación eliminada"}
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=400, detail=str(e))


# ── PROGRESO POR CARRERA ──────────────────────────────────────────────────────
@router.get("/carrera/{carrera_id}/progreso")
def obtener_progreso_por_carrera(carrera_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT carrera_id FROM carrera WHERE carrera_id = %s", (carrera_id,))
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Carrera no encontrada")

        cols_est = _columnas_tabla(cursor, 'estudiante')
        extra_est = ""
        if 'codigo_estudiante' in cols_est:
            extra_est += ", e.codigo_estudiante"
        if 'promedio_general' in cols_est:
            extra_est += ", e.promedio_general"
        if 'estado_academico' in cols_est:
            extra_est += ", e.estado_academico"

        cursor.execute(f"""
            SELECT e.estudiante_id, e.nombre {extra_est},
                COUNT(DISTINCT c.calificacion_id) as total_calificaciones,
                COUNT(DISTINCT CASE WHEN c.estado = 'aprobado' THEN c.calificacion_id END) as materias_aprobadas,
                COUNT(DISTINCT CASE WHEN c.estado = 'reprobado' THEN c.calificacion_id END) as materias_reprobadas,
                AVG(c.nota_final) as promedio_calculado
            FROM estudiante e
            LEFT JOIN calificacion c ON e.estudiante_id = c.estudiante_id
            WHERE e.carrera_id = %s
            GROUP BY e.estudiante_id
            ORDER BY e.nombre
        """, (carrera_id,))
        estudiantes = cursor.fetchall()

        estudiantes_detalle = []
        for est in estudiantes:
            cursor.execute("""
                SELECT c.calificacion_id, m.nombre as materia_nombre,
                       c.nota_parcial1, c.nota_parcial2,
                       c.nota_final, c.estado, c.semestre
                FROM calificacion c
                JOIN materia m ON c.materia_id = m.materia_id
                WHERE c.estudiante_id = %s
                ORDER BY c.semestre, m.nombre
            """, (est['estudiante_id'],))
            calificaciones = cursor.fetchall()
            estudiantes_detalle.append({**est, 'calificaciones': calificaciones})

        cursor.close()
        return {
            'carrera_id': carrera_id,
            'total_estudiantes': len(estudiantes_detalle),
            'estudiantes': estudiantes_detalle
        }
    except HTTPException:
        raise
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/carrera/{carrera_id}/lista-simple")
def obtener_lista_estudiantes_carrera(carrera_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cols_est = _columnas_tabla(cursor, 'estudiante')
        extra = ""
        if 'codigo_estudiante' in cols_est:
            extra += ", e.codigo_estudiante"
        if 'promedio_general' in cols_est:
            extra += ", e.promedio_general"
        if 'estado_academico' in cols_est:
            extra += ", e.estado_academico"

        cursor.execute(f"""
            SELECT e.estudiante_id, e.nombre {extra}
            FROM estudiante e
            WHERE e.carrera_id = %s
            ORDER BY e.nombre
        """, (carrera_id,))
        estudiantes = cursor.fetchall()
        cursor.close()
        return estudiantes if estudiantes else []
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/carrera/{carrera_id}/estadisticas")
def obtener_estadisticas_carrera(carrera_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cols_est = _columnas_tabla(cursor, 'estudiante')
        extra_counts = ""
        if 'estado_academico' in cols_est:
            extra_counts = """
                COUNT(DISTINCT CASE WHEN e.estado_academico = 'excelente' THEN e.estudiante_id END) as excelentes,
                COUNT(DISTINCT CASE WHEN e.estado_academico = 'bueno' THEN e.estudiante_id END) as buenos,
                COUNT(DISTINCT CASE WHEN e.estado_academico = 'regular' THEN e.estudiante_id END) as regulares,
                COUNT(DISTINCT CASE WHEN e.estado_academico = 'riesgo' THEN e.estudiante_id END) as en_riesgo,
            """
        avg_extra = ", AVG(e.promedio_general) as promedio_carrera" if 'promedio_general' in cols_est else ", AVG(c.nota_final) as promedio_carrera"

        cursor.execute(f"""
            SELECT
                COUNT(DISTINCT e.estudiante_id) as total_estudiantes,
                {extra_counts}
                {avg_extra},
                COUNT(c.calificacion_id) as total_calificaciones,
                COUNT(CASE WHEN c.estado = 'aprobado' THEN 1 END) as calificaciones_aprobadas,
                COUNT(CASE WHEN c.estado = 'reprobado' THEN 1 END) as calificaciones_reprobadas
            FROM estudiante e
            LEFT JOIN calificacion c ON e.estudiante_id = c.estudiante_id
            WHERE e.carrera_id = %s
        """, (carrera_id,))
        stats = cursor.fetchone()
        cursor.close()
        if not stats:
            raise HTTPException(status_code=404, detail="Carrera no encontrada")
        return stats
    except HTTPException:
        raise
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")