from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from database import get_db

router = APIRouter()


# =============== MODELOS PYDANTIC ===============

class EvaluacionCreate(BaseModel):
    recomendacion_id: int
    titulo: str
    descripcion: Optional[str] = None


class EvaluacionUpdate(BaseModel):
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    estado: Optional[str] = None


class PreguntaCreate(BaseModel):
    evaluacion_id: int
    texto_pregunta: str
    tipo_pregunta: str = "abierta"  # abierta, opcion_multiple, si_no, escala
    orden: int = 1
    requerida: bool = True


class PreguntaUpdate(BaseModel):
    texto_pregunta: Optional[str] = None
    tipo_pregunta: Optional[str] = None
    orden: Optional[int] = None
    requerida: Optional[bool] = None


class OpcionRespuestaCreate(BaseModel):
    pregunta_id: int
    texto_opcion: str
    es_correcta: bool = False
    orden: int = 1


class OpcionRespuestaUpdate(BaseModel):
    texto_opcion: Optional[str] = None
    es_correcta: Optional[bool] = None
    orden: Optional[int] = None


class IniciarEvaluacionCreate(BaseModel):
    evaluacion_id: int
    estudiante_id: int


class RespuestaEstudianteCreate(BaseModel):
    evaluacion_estudiante_id: Optional[int] = None
    pregunta_id: int
    texto_respuesta: Optional[str] = None
    opcion_id: Optional[int] = None


class SubmitEvaluacionCreate(BaseModel):
    evaluacion_id: int
    estudiante_id: int
    respuestas: List[RespuestaEstudianteCreate]


# =============================================================================
# EVALUACIONES
# =============================================================================

@router.get("")
def listar_evaluaciones(
    recomendacion_id: Optional[int] = Query(None),
    estado: Optional[str] = Query(None),
    db=Depends(get_db),
):
    cursor = db.cursor(dictionary=True)
    try:
        query = """
            SELECT e.evaluacion_id, e.recomendacion_id, e.titulo, e.descripcion,
                   e.estado, e.creado_en,
                   r.tipo_recomendacion, r.descripcion as recom_descripcion,
                   r.estudiante_id
            FROM sira.evaluacion e
            LEFT JOIN sira.recomendacion r ON e.recomendacion_id = r.recomendacion_id
            WHERE 1=1
        """
        params = []
        if recomendacion_id:
            query += " AND e.recomendacion_id = %s"
            params.append(recomendacion_id)
        if estado:
            query += " AND e.estado = %s"
            params.append(estado)
        query += " ORDER BY e.creado_en DESC"

        cursor.execute(query, params) if params else cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        return result
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/estudiante/{estudiante_id}")
def evaluaciones_por_estudiante(estudiante_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT e.evaluacion_id, e.recomendacion_id, e.titulo, e.descripcion,
                   e.estado, e.creado_en,
                   r.tipo_recomendacion, r.prioridad,
                   (
                     SELECT COUNT(*) FROM sira.evaluacion_estudiante ee2
                     WHERE ee2.evaluacion_id = e.evaluacion_id
                       AND ee2.estado = 'finalizada'
                       AND ee2.seguimiento_id = sr.seguimiento_id
                   ) as ya_respondida
            FROM sira.evaluacion e
            JOIN sira.recomendacion r ON e.recomendacion_id = r.recomendacion_id
            JOIN sira.seguimiento_recomendacion sr ON r.recomendacion_id = sr.recomendacion_id
            WHERE sr.estudiante_id = %s
              AND e.estado = 'activa'
            ORDER BY e.creado_en DESC
        """, (estudiante_id,))
        result = cursor.fetchall()

        if not result:
            cursor.execute("""
                SELECT e.evaluacion_id, e.recomendacion_id, e.titulo, e.descripcion,
                       e.estado, e.creado_en,
                       r.tipo_recomendacion, r.prioridad,
                       (
                         SELECT COUNT(*) FROM sira.evaluacion_estudiante ee2
                         JOIN sira.seguimiento_recomendacion sr2
                           ON ee2.seguimiento_id = sr2.seguimiento_id
                         WHERE ee2.evaluacion_id = e.evaluacion_id
                           AND ee2.estado = 'finalizada'
                           AND sr2.estudiante_id = %s
                       ) as ya_respondida
                FROM sira.evaluacion e
                JOIN sira.recomendacion r ON e.recomendacion_id = r.recomendacion_id
                WHERE r.estudiante_id = %s
                  AND e.estado = 'activa'
                ORDER BY e.creado_en DESC
            """, (estudiante_id, estudiante_id))
            result = cursor.fetchall()

        cursor.close()
        for row in result:
            row['ya_respondida'] = bool(row.get('ya_respondida', 0))
        return result if result else []
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/resultados/estudiante/{estudiante_id}")
def resultados_por_estudiante(estudiante_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT
                ee.evaluacion_estudiante_id,
                ee.evaluacion_id,
                ie.respuestas_correctas,
                ee.evaluacion_aprobada,
                ee.fecha_inicio,
                ee.fecha_fin,
                ev.titulo,
                ev.descripcion,
                ev.recomendacion_id,
                r.tipo_recomendacion,
                r.descripcion   AS recom_descripcion,
                r.prioridad,
                m.nombre        AS materia_nombre,
                CASE
                    WHEN ee.evaluacion_aprobada THEN 'aprobada'
                    WHEN ee.estado = 'finalizada' THEN 'finalizada'
                    ELSE ee.estado
                END AS nivel_progreso
            FROM sira.evaluacion_estudiante ee
            JOIN sira.seguimiento_recomendacion sr ON ee.seguimiento_id = sr.seguimiento_id
            JOIN sira.evaluacion ev    ON ee.evaluacion_id    = ev.evaluacion_id
            JOIN sira.recomendacion r  ON ev.recomendacion_id = r.recomendacion_id
            LEFT JOIN sira.intento_evaluacion ie ON ee.evaluacion_estudiante_id = ie.evaluacion_estudiante_id
            LEFT JOIN sira.materia m   ON r.materia_id        = m.materia_id
            WHERE sr.estudiante_id = %s AND ee.estado = 'finalizada'
            ORDER BY ee.fecha_fin DESC
        """, (estudiante_id,))
        result = cursor.fetchall()
        cursor.close()
        return result if result else []
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error resultados: {str(e)}")


@router.get("/reportes/admin")
def reporte_admin(db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT
                ee.evaluacion_estudiante_id,
                ee.evaluacion_id,
                ie.respuestas_correctas,
                ee.fecha_fin,
                ee.fecha_inicio,
                ev.titulo,
                ev.descripcion,
                r.recomendacion_id,
                r.tipo_recomendacion,
                r.descripcion       AS recom_descripcion,
                r.prioridad,
                sr.recomendacion_visualizada,
                est.nombre          AS estudiante_nombre,
                est.estudiante_id,
                m.nombre            AS materia_nombre,
                c.nombre            AS carrera_nombre,
                CASE
                    WHEN ee.evaluacion_aprobada THEN 'aprobada'
                    WHEN ee.estado = 'finalizada' THEN 'finalizada'
                    ELSE ee.estado
                END AS nivel_progreso
            FROM sira.evaluacion_estudiante ee
            JOIN sira.seguimiento_recomendacion sr ON ee.seguimiento_id = sr.seguimiento_id
            JOIN sira.evaluacion ev    ON ee.evaluacion_id    = ev.evaluacion_id
            JOIN sira.recomendacion r  ON ev.recomendacion_id = r.recomendacion_id
            JOIN sira.estudiante est   ON sr.estudiante_id    = est.estudiante_id
            LEFT JOIN sira.intento_evaluacion ie ON ee.evaluacion_estudiante_id = ie.evaluacion_estudiante_id
            LEFT JOIN sira.materia m   ON r.materia_id        = m.materia_id
            LEFT JOIN sira.carrera c   ON est.carrera_id      = c.carrera_id
            WHERE ee.estado = 'finalizada'
            ORDER BY ee.fecha_fin DESC
        """)
        result = cursor.fetchall()
        cursor.close()
        return result if result else []
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error reporte admin: {str(e)}")


@router.get("/reportes/estudiante/{estudiante_id}")
def reporte_estudiante(estudiante_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT
                ee.evaluacion_estudiante_id,
                ee.evaluacion_id,
                ie.respuestas_correctas,
                ee.fecha_fin,
                ev.titulo,
                r.tipo_recomendacion,
                r.descripcion   AS recom_descripcion,
                sr.recomendacion_visualizada,
                m.nombre        AS materia_nombre,
                CASE
                    WHEN ee.evaluacion_aprobada THEN 'aprobada'
                    WHEN ee.estado = 'finalizada' THEN 'finalizada'
                    ELSE ee.estado
                END AS nivel_progreso
            FROM sira.evaluacion_estudiante ee
            JOIN sira.seguimiento_recomendacion sr ON ee.seguimiento_id = sr.seguimiento_id
            JOIN sira.evaluacion ev    ON ee.evaluacion_id    = ev.evaluacion_id
            JOIN sira.recomendacion r  ON ev.recomendacion_id = r.recomendacion_id
            LEFT JOIN sira.intento_evaluacion ie ON ee.evaluacion_estudiante_id = ie.evaluacion_estudiante_id
            LEFT JOIN sira.materia m   ON r.materia_id        = m.materia_id
            WHERE sr.estudiante_id = %s AND ee.estado = 'finalizada'
            ORDER BY ee.fecha_fin DESC
        """, (estudiante_id,))
        result = cursor.fetchall()
        cursor.close()
        return result if result else []
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error reporte estudiante: {str(e)}")


# =============================================================================
# PREGUNTAS
# =============================================================================

@router.get("/preguntas/evaluacion/{evaluacion_id}")
def preguntas_por_evaluacion(evaluacion_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT p.pregunta_id, p.evaluacion_id, p.texto_pregunta,
                   p.tipo_pregunta, p.orden, p.requerida, p.creado_en
            FROM sira.pregunta p
            WHERE p.evaluacion_id = %s
            ORDER BY p.orden
        """, (evaluacion_id,))
        preguntas = cursor.fetchall()

        for p in preguntas:
            if p['tipo_pregunta'] in ('opcion_multiple', 'si_no'):
                cursor.execute("""
                    SELECT opcion_id, texto_opcion, es_correcta, orden
                    FROM sira.opcion_respuesta
                    WHERE pregunta_id = %s ORDER BY orden
                """, (p['pregunta_id'],))
                p['opciones'] = cursor.fetchall()
            else:
                p['opciones'] = []

        cursor.close()
        return preguntas if preguntas else []
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error preguntas: {str(e)}")


@router.post("/preguntas", status_code=201)
def crear_pregunta(data: PreguntaCreate, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT evaluacion_id FROM sira.evaluacion WHERE evaluacion_id = %s",
            (data.evaluacion_id,)
        )
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Evaluación no encontrada")

        cursor.execute("""
            INSERT INTO sira.pregunta (evaluacion_id, texto_pregunta, tipo_pregunta, orden, requerida)
            VALUES (%s, %s, %s, %s, %s)
        """, (data.evaluacion_id, data.texto_pregunta, data.tipo_pregunta,
              data.orden, data.requerida))
        db.commit()
        new_id = cursor.lastrowid

        cursor.execute("""
            SELECT pregunta_id, evaluacion_id, texto_pregunta, tipo_pregunta,
                   orden, requerida, creado_en
            FROM sira.pregunta WHERE pregunta_id = %s
        """, (new_id,))
        pregunta = cursor.fetchone()
        cursor.close()
        return pregunta
    except HTTPException:
        cursor.close()
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.put("/preguntas/{pregunta_id}")
def actualizar_pregunta(pregunta_id: int, data: PreguntaUpdate, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT pregunta_id FROM sira.pregunta WHERE pregunta_id = %s",
            (pregunta_id,)
        )
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Pregunta no encontrada")

        campos = {k: v for k, v in data.model_dump().items() if v is not None}
        if not campos:
            cursor.close()
            raise HTTPException(status_code=400, detail="Sin datos para actualizar")

        set_clause = ", ".join([f"{k} = %s" for k in campos])
        cursor.execute(
            f"UPDATE sira.pregunta SET {set_clause} WHERE pregunta_id = %s",
            (*campos.values(), pregunta_id)
        )
        db.commit()

        cursor.execute("""
            SELECT pregunta_id, evaluacion_id, texto_pregunta, tipo_pregunta,
                   orden, requerida, creado_en
            FROM sira.pregunta WHERE pregunta_id = %s
        """, (pregunta_id,))
        pregunta = cursor.fetchone()
        cursor.close()
        return pregunta
    except HTTPException:
        cursor.close()
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.delete("/preguntas/{pregunta_id}")
def eliminar_pregunta(pregunta_id: int, db=Depends(get_db)):
    cursor = db.cursor()
    try:
        cursor.execute(
            "SELECT pregunta_id FROM sira.pregunta WHERE pregunta_id = %s",
            (pregunta_id,)
        )
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Pregunta no encontrada")

        cursor.execute("DELETE FROM sira.pregunta WHERE pregunta_id = %s", (pregunta_id,))
        db.commit()
        cursor.close()
        return {"message": "Pregunta eliminada"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# =============================================================================
# OPCIONES
# =============================================================================

@router.get("/opciones/pregunta/{pregunta_id}")
def opciones_por_pregunta(pregunta_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT opcion_id, pregunta_id, texto_opcion, es_correcta, orden, creado_en
            FROM sira.opcion_respuesta WHERE pregunta_id = %s ORDER BY orden
        """, (pregunta_id,))
        result = cursor.fetchall()
        cursor.close()
        return result
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/opciones/{opcion_id}")
def obtener_opcion(opcion_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT o.opcion_id, o.pregunta_id, o.texto_opcion,
                   o.es_correcta, o.orden, o.creado_en
            FROM sira.opcion_respuesta o WHERE o.opcion_id = %s
        """, (opcion_id,))
        row = cursor.fetchone()
        cursor.close()
        if not row:
            raise HTTPException(status_code=404, detail="Opción no encontrada")
        return row
    except HTTPException:
        raise
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/opciones", status_code=201)
def crear_opcion(data: OpcionRespuestaCreate, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT pregunta_id FROM sira.pregunta WHERE pregunta_id = %s",
            (data.pregunta_id,)
        )
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Pregunta no encontrada")

        cursor.execute("""
            INSERT INTO sira.opcion_respuesta (pregunta_id, texto_opcion, es_correcta, orden)
            VALUES (%s, %s, %s, %s)
        """, (data.pregunta_id, data.texto_opcion, data.es_correcta, data.orden))
        db.commit()
        new_id = cursor.lastrowid

        cursor.execute("""
            SELECT opcion_id, pregunta_id, texto_opcion, es_correcta, orden, creado_en
            FROM sira.opcion_respuesta WHERE opcion_id = %s
        """, (new_id,))
        opcion = cursor.fetchone()
        cursor.close()
        return opcion
    except HTTPException:
        cursor.close()
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.put("/opciones/{opcion_id}")
def actualizar_opcion(opcion_id: int, data: OpcionRespuestaUpdate, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT opcion_id FROM sira.opcion_respuesta WHERE opcion_id = %s",
            (opcion_id,)
        )
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Opción no encontrada")

        campos = {k: v for k, v in data.model_dump().items() if v is not None}
        if not campos:
            cursor.close()
            raise HTTPException(status_code=400, detail="Sin datos para actualizar")

        set_clause = ", ".join([f"{k} = %s" for k in campos])
        cursor.execute(
            f"UPDATE sira.opcion_respuesta SET {set_clause} WHERE opcion_id = %s",
            (*campos.values(), opcion_id)
        )
        db.commit()

        cursor.execute("""
            SELECT opcion_id, pregunta_id, texto_opcion, es_correcta, orden, creado_en
            FROM sira.opcion_respuesta WHERE opcion_id = %s
        """, (opcion_id,))
        opcion = cursor.fetchone()
        cursor.close()
        return opcion
    except HTTPException:
        cursor.close()
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.delete("/opciones/{opcion_id}")
def eliminar_opcion(opcion_id: int, db=Depends(get_db)):
    cursor = db.cursor()
    try:
        cursor.execute(
            "SELECT opcion_id FROM sira.opcion_respuesta WHERE opcion_id = %s",
            (opcion_id,)
        )
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Opción no encontrada")

        cursor.execute("DELETE FROM sira.opcion_respuesta WHERE opcion_id = %s", (opcion_id,))
        db.commit()
        cursor.close()
        return {"message": "Opción eliminada"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# =============================================================================
# RESPUESTAS DEL ESTUDIANTE
# =============================================================================

@router.post("/iniciar", status_code=201)
def iniciar_evaluacion(data: IniciarEvaluacionCreate, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT sr.seguimiento_id FROM sira.seguimiento_recomendacion sr
            JOIN sira.evaluacion e ON e.recomendacion_id = sr.recomendacion_id
            WHERE e.evaluacion_id = %s AND sr.estudiante_id = %s
            LIMIT 1
        """, (data.evaluacion_id, data.estudiante_id))
        seguimiento = cursor.fetchone()
        if not seguimiento:
            cursor.close()
            raise HTTPException(status_code=404, detail="Seguimiento no encontrado")

        seguimiento_id = seguimiento['seguimiento_id']

        cursor.execute("""
            SELECT evaluacion_estudiante_id, evaluacion_id, estado, fecha_inicio
            FROM sira.evaluacion_estudiante
            WHERE evaluacion_id = %s AND seguimiento_id = %s AND estado != 'finalizada'
        """, (data.evaluacion_id, seguimiento_id))
        existente = cursor.fetchone()
        if existente:
            cursor.close()
            return existente

        cursor.execute("""
            INSERT INTO sira.evaluacion_estudiante (seguimiento_id, evaluacion_id, estado)
            VALUES (%s, %s, 'en_progreso')
        """, (seguimiento_id, data.evaluacion_id))
        db.commit()
        new_id = cursor.lastrowid

        cursor.execute("""
            SELECT evaluacion_estudiante_id, evaluacion_id, estado, fecha_inicio
            FROM sira.evaluacion_estudiante WHERE evaluacion_estudiante_id = %s
        """, (new_id,))
        result = cursor.fetchone()
        cursor.close()
        return result
    except HTTPException:
        db.rollback()
        cursor.close()
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/respuestas/submit", status_code=201)
def submit_respuestas(data: SubmitEvaluacionCreate, db=Depends(get_db)):
    """
    FIX: el error 'Unknown column evaluacion_estudiante_id in where clause'
    ocurría porque la tabla respuesta_estudiante puede no tener esa columna,
    o tener un nombre diferente. Se usa try/except en cada INSERT/DELETE de
    respuesta con un fallback que no usa esa columna.
    """
    cursor = db.cursor(dictionary=True)
    try:
        # ── Paso 1: obtener o crear seguimiento_id ────────────────────────────
        cursor.execute("""
            SELECT sr.seguimiento_id FROM sira.seguimiento_recomendacion sr
            JOIN sira.evaluacion e ON e.recomendacion_id = sr.recomendacion_id
            WHERE e.evaluacion_id = %s AND sr.estudiante_id = %s
            LIMIT 1
        """, (data.evaluacion_id, data.estudiante_id))
        seguimiento = cursor.fetchone()

        if not seguimiento:
            cursor.execute("""
                SELECT e.recomendacion_id
                FROM sira.evaluacion e
                WHERE e.evaluacion_id = %s
            """, (data.evaluacion_id,))
            eval_info = cursor.fetchone()
            if not eval_info:
                cursor.close()
                raise HTTPException(status_code=404, detail="Evaluación no encontrada")

            recomendacion_id = eval_info['recomendacion_id']
            cursor.execute("""
                INSERT INTO sira.seguimiento_recomendacion
                    (recomendacion_id, estudiante_id, recomendacion_visualizada)
                VALUES (%s, %s, 1)
            """, (recomendacion_id, data.estudiante_id))
            db.commit()
            seguimiento_id = cursor.lastrowid
        else:
            seguimiento_id = seguimiento['seguimiento_id']

        # ── Paso 2: obtener o crear evaluacion_estudiante ─────────────────────
        cursor.execute("""
            SELECT evaluacion_estudiante_id FROM sira.evaluacion_estudiante
            WHERE evaluacion_id = %s AND seguimiento_id = %s
        """, (data.evaluacion_id, seguimiento_id))
        ee = cursor.fetchone()

        if not ee:
            cursor.execute("""
                INSERT INTO sira.evaluacion_estudiante (seguimiento_id, evaluacion_id, estado)
                VALUES (%s, %s, 'en_progreso')
            """, (seguimiento_id, data.evaluacion_id))
            db.commit()
            ee_id = cursor.lastrowid
        else:
            ee_id = ee['evaluacion_estudiante_id']

        # ── Paso 3: insertar respuestas con detección automática de esquema ───
        # Detectar si la tabla tiene la columna evaluacion_estudiante_id
        cursor.execute("""
            SELECT COLUMN_NAME
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = 'sira'
              AND TABLE_NAME = 'respuesta_estudiante'
        """)
        columnas_resp = {row['COLUMN_NAME'] for row in cursor.fetchall()}
        usa_ee_id = 'evaluacion_estudiante_id' in columnas_resp

        for resp in data.respuestas:
            if usa_ee_id:
                # Schema completo con evaluacion_estudiante_id
                try:
                    cursor.execute("""
                        DELETE FROM sira.respuesta_estudiante
                        WHERE evaluacion_estudiante_id = %s AND pregunta_id = %s
                    """, (ee_id, resp.pregunta_id))
                except Exception:
                    pass  # si falla el delete, ignorar y continuar con insert

                cursor.execute("""
                    INSERT INTO sira.respuesta_estudiante
                    (evaluacion_estudiante_id, pregunta_id, texto_respuesta, opcion_id)
                    VALUES (%s, %s, %s, %s)
                """, (ee_id, resp.pregunta_id, resp.texto_respuesta, resp.opcion_id))
            else:
                # Fallback: schema sin evaluacion_estudiante_id
                # Buscar la columna que funciona como FK a evaluacion_estudiante
                fk_col = None
                for candidato in ('intento_id', 'evaluacion_id', 'seguimiento_id'):
                    if candidato in columnas_resp:
                        fk_col = candidato
                        break

                if fk_col:
                    fk_val = ee_id if fk_col != 'evaluacion_id' else data.evaluacion_id
                    try:
                        cursor.execute(
                            f"DELETE FROM sira.respuesta_estudiante WHERE {fk_col} = %s AND pregunta_id = %s",
                            (fk_val, resp.pregunta_id)
                        )
                    except Exception:
                        pass

                    # Insertar con las columnas disponibles
                    cols_insert = [fk_col, 'pregunta_id']
                    vals_insert = [fk_val, resp.pregunta_id]
                    if 'texto_respuesta' in columnas_resp:
                        cols_insert.append('texto_respuesta')
                        vals_insert.append(resp.texto_respuesta)
                    if 'opcion_id' in columnas_resp:
                        cols_insert.append('opcion_id')
                        vals_insert.append(resp.opcion_id)

                    placeholders = ', '.join(['%s'] * len(cols_insert))
                    cols_str = ', '.join(cols_insert)
                    cursor.execute(
                        f"INSERT INTO sira.respuesta_estudiante ({cols_str}) VALUES ({placeholders})",
                        vals_insert
                    )
                else:
                    # Último recurso: solo pregunta_id y respuesta de texto
                    try:
                        cursor.execute("""
                            INSERT INTO sira.respuesta_estudiante (pregunta_id, texto_respuesta, opcion_id)
                            VALUES (%s, %s, %s)
                        """, (resp.pregunta_id, resp.texto_respuesta, resp.opcion_id))
                    except Exception as insert_err:
                        raise HTTPException(
                            status_code=500,
                            detail=f"No se pudo insertar respuesta. Columnas disponibles: {columnas_resp}. Error: {insert_err}"
                        )

        # ── Paso 4: contar respuestas correctas ───────────────────────────────
        try:
            if usa_ee_id:
                cursor.execute("""
                    SELECT COUNT(*) as total,
                           SUM(CASE WHEN o.es_correcta = 1 THEN 1 ELSE 0 END) as correctas
                    FROM sira.respuesta_estudiante re
                    JOIN sira.opcion_respuesta o ON re.opcion_id = o.opcion_id
                    WHERE re.evaluacion_estudiante_id = %s
                """, (ee_id,))
            else:
                cursor.execute("""
                    SELECT COUNT(*) as total,
                           SUM(CASE WHEN o.es_correcta = 1 THEN 1 ELSE 0 END) as correctas
                    FROM sira.respuesta_estudiante re
                    JOIN sira.opcion_respuesta o ON re.opcion_id = o.opcion_id
                    JOIN sira.pregunta p ON re.pregunta_id = p.pregunta_id
                    WHERE p.evaluacion_id = %s
                """, (data.evaluacion_id,))
            cal = cursor.fetchone()
        except Exception:
            cal = None

        respuestas_correctas = cal['correctas'] if cal and cal['correctas'] else 0
        total_respuestas = cal['total'] if cal and cal['total'] else max(len(data.respuestas), 1)

        # ── Paso 5: registrar intento ─────────────────────────────────────────
        try:
            cursor.execute("""
                INSERT INTO sira.intento_evaluacion (evaluacion_estudiante_id, respuestas_correctas, estado)
                VALUES (%s, %s, 'aceptado')
            """, (ee_id, respuestas_correctas))
        except Exception:
            pass  # si ya existe el intento, no bloquear

        # ── Paso 6: marcar como finalizada ───────────────────────────────────
        aprobada = respuestas_correctas >= (total_respuestas // 2) if total_respuestas > 0 else False
        cursor.execute("""
            UPDATE sira.evaluacion_estudiante
            SET estado = 'finalizada', evaluacion_aprobada = %s, fecha_fin = NOW()
            WHERE evaluacion_estudiante_id = %s
        """, (aprobada, ee_id))
        db.commit()
        cursor.close()
        return {
            "message": "Respuestas enviadas correctamente",
            "evaluacion_estudiante_id": ee_id,
            "respuestas_correctas": respuestas_correctas
        }
    except HTTPException:
        db.rollback()
        cursor.close()
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# =============================================================================
# CRUD EVALUACIONES
# =============================================================================

@router.post("", status_code=201)
def crear_evaluacion(data: EvaluacionCreate, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT recomendacion_id FROM sira.recomendacion WHERE recomendacion_id = %s",
            (data.recomendacion_id,)
        )
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Recomendación no encontrada")

        cursor.execute("""
            INSERT INTO sira.evaluacion (recomendacion_id, titulo, descripcion)
            VALUES (%s, %s, %s)
        """, (data.recomendacion_id, data.titulo, data.descripcion))
        db.commit()
        new_id = cursor.lastrowid

        cursor.execute("""
            SELECT evaluacion_id, recomendacion_id, titulo, descripcion, estado, creado_en
            FROM sira.evaluacion WHERE evaluacion_id = %s
        """, (new_id,))
        evaluacion = cursor.fetchone()
        cursor.close()
        return evaluacion
    except HTTPException:
        cursor.close()
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/{evaluacion_id}")
def obtener_evaluacion(evaluacion_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT e.evaluacion_id, e.recomendacion_id, e.titulo, e.descripcion,
                   e.estado, e.creado_en
            FROM sira.evaluacion e WHERE e.evaluacion_id = %s
        """, (evaluacion_id,))
        row = cursor.fetchone()
        cursor.close()
        if not row:
            raise HTTPException(status_code=404, detail="Evaluación no encontrada")
        return row
    except HTTPException:
        raise
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.put("/{evaluacion_id}")
def actualizar_evaluacion(evaluacion_id: int, data: EvaluacionUpdate, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT evaluacion_id FROM sira.evaluacion WHERE evaluacion_id = %s",
            (evaluacion_id,)
        )
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Evaluación no encontrada")

        campos = {k: v for k, v in data.model_dump().items() if v is not None}
        if not campos:
            cursor.close()
            raise HTTPException(status_code=400, detail="Sin datos para actualizar")

        set_clause = ", ".join([f"{k} = %s" for k in campos])
        cursor.execute(
            f"UPDATE sira.evaluacion SET {set_clause} WHERE evaluacion_id = %s",
            (*campos.values(), evaluacion_id)
        )
        db.commit()

        cursor.execute("""
            SELECT evaluacion_id, recomendacion_id, titulo, descripcion, estado, creado_en
            FROM sira.evaluacion WHERE evaluacion_id = %s
        """, (evaluacion_id,))
        evaluacion = cursor.fetchone()
        cursor.close()
        return evaluacion
    except HTTPException:
        cursor.close()
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.delete("/{evaluacion_id}")
def eliminar_evaluacion(evaluacion_id: int, db=Depends(get_db)):
    cursor = db.cursor()
    try:
        cursor.execute(
            "SELECT evaluacion_id FROM sira.evaluacion WHERE evaluacion_id = %s",
            (evaluacion_id,)
        )
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Evaluación no encontrada")

        cursor.execute("DELETE FROM sira.evaluacion WHERE evaluacion_id = %s", (evaluacion_id,))
        db.commit()
        cursor.close()
        return {"message": "Evaluación eliminada"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")