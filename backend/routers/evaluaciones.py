from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from database import get_db
from mysql.connector import errors as mysql_errors

router = APIRouter()

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
    tipo_pregunta: str = "abierta"
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

_COLUMNAS_CACHE: Optional[dict] = None

def _columnas_respuesta(cursor) -> dict:
    global _COLUMNAS_CACHE
    if _COLUMNAS_CACHE is not None:
        return _COLUMNAS_CACHE

    try:
        cursor.execute("""
            SELECT COLUMN_NAME FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME   = 'respuesta_estudiante'
            ORDER BY ORDINAL_POSITION
        """)
        cols = {r['COLUMN_NAME'] for r in cursor.fetchall()}
        _COLUMNAS_CACHE = {
            'tiene_ee_id':      'evaluacion_estudiante_id' in cols,
            'tiene_est_id':     'estudiante_id'            in cols,
            'tiene_texto':      'texto_respuesta'          in cols,
            'tiene_respuesta':  'respuesta'                in cols,
            'tiene_respuesta_texto': 'respuesta_texto'     in cols,
            'todas':            cols,
        }
        return _COLUMNAS_CACHE
    except Exception as e:
        return {
            'tiene_ee_id':      True,
            'tiene_est_id':     False,
            'tiene_texto':      True,
            'tiene_respuesta':  False,
            'tiene_respuesta_texto': False,
            'todas':            set(),
        }

def _col_texto(info: dict) -> str:
    # La columna real en la DB es 'respuesta_texto'
    if info['tiene_respuesta_texto']: return 'respuesta_texto'
    if info['tiene_texto']: return 'texto_respuesta'
    if info['tiene_respuesta']: return 'respuesta'
    return 'respuesta_texto'

def _col_id_estudiante(info: dict) -> Optional[str]:
    if info['tiene_ee_id']: return 'evaluacion_estudiante_id'
    if info['tiene_est_id']: return 'estudiante_id'
    return None

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

@router.get("/respuestas/evaluacion/{evaluacion_id}/estudiante/{estudiante_id}")
def respuestas_por_evaluacion_estudiante(evaluacion_id: int, estudiante_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT
                re.respuesta_id,
                re.pregunta_id,
                re.opcion_id,
                re.respuesta_texto,
                re.es_correcta,
                re.calificacion_estrellas, 
                re.retroalimentacion_maestro,
                re.retroalimentacion_like_alumno,
                re.fecha_like_retroalimentacion,
                re.creado_en,
                p.texto_pregunta,
                p.tipo_pregunta,
                p.orden
            FROM sira.respuesta_estudiante re
            JOIN sira.intento_evaluacion ie ON re.intento_id = ie.intento_id
            JOIN sira.evaluacion_estudiante ee ON ie.evaluacion_estudiante_id = ee.evaluacion_estudiante_id
            JOIN sira.seguimiento_recomendacion sr ON ee.seguimiento_id = sr.seguimiento_id
            JOIN sira.pregunta p ON re.pregunta_id = p.pregunta_id
            WHERE ee.evaluacion_id = %s
              AND sr.estudiante_id = %s
            ORDER BY p.orden
        """, (evaluacion_id, estudiante_id))
        result = cursor.fetchall()
        cursor.close()
        return result if result else []
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error respuestas: {str(e)}")

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
    cursor = db.cursor(dictionary=True)
    try:
        if not data.respuestas:
            raise HTTPException(
                status_code=400,
                detail="No se puede enviar una evaluación sin respuestas"
            )

        cursor.execute("""
            SELECT pregunta_id
            FROM sira.pregunta
            WHERE evaluacion_id = %s
            ORDER BY orden
        """, (data.evaluacion_id,))
        preguntas_eval = cursor.fetchall()
        if not preguntas_eval:
            raise HTTPException(
                status_code=400,
                detail="La evaluación no tiene preguntas registradas"
            )

        ids_preguntas = {int(p['pregunta_id']) for p in preguntas_eval}
        respuestas_validas = {}
        for resp in data.respuestas:
            if int(resp.pregunta_id) not in ids_preguntas:
                raise HTTPException(
                    status_code=400,
                    detail=f"La pregunta {resp.pregunta_id} no pertenece a esta evaluación"
                )
            tiene_texto = resp.texto_respuesta is not None and resp.texto_respuesta.strip() != ''
            tiene_opcion = resp.opcion_id is not None
            if not tiene_texto and not tiene_opcion:
                raise HTTPException(
                    status_code=400,
                    detail=f"La pregunta {resp.pregunta_id} no tiene respuesta"
                )
            respuestas_validas[int(resp.pregunta_id)] = True

        faltantes = [str(pid) for pid in ids_preguntas if pid not in respuestas_validas]
        if faltantes:
            raise HTTPException(
                status_code=400,
                detail="Faltan respuestas para las preguntas: " + ", ".join(faltantes)
            )

        info     = _columnas_respuesta(cursor)
        col_txt  = _col_texto(info)           
        col_link = _col_id_estudiante(info)   
        usa_ee   = info['tiene_ee_id']        

        cursor.execute("""
            SELECT sr.seguimiento_id FROM sira.seguimiento_recomendacion sr
            JOIN sira.evaluacion e ON e.recomendacion_id = sr.recomendacion_id
            WHERE e.evaluacion_id = %s AND sr.estudiante_id = %s
            LIMIT 1
        """, (data.evaluacion_id, data.estudiante_id))
        seguimiento = cursor.fetchone()

        if not seguimiento:
            cursor.execute(
                "SELECT recomendacion_id FROM sira.evaluacion WHERE evaluacion_id = %s",
                (data.evaluacion_id,)
            )
            eval_info = cursor.fetchone()
            if not eval_info:
                raise HTTPException(status_code=404, detail="Evaluación no encontrada")

            cursor.execute("""
                INSERT INTO sira.seguimiento_recomendacion
                    (recomendacion_id, estudiante_id, recomendacion_visualizada)
                VALUES (%s, %s, 1)
            """, (eval_info['recomendacion_id'], data.estudiante_id))
            db.commit()
            seguimiento_id = cursor.lastrowid
        else:
            seguimiento_id = seguimiento['seguimiento_id']

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

        intento_id = None
        try:
            cursor.execute("""
                SELECT COLUMN_NAME FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'intento_evaluacion'
                ORDER BY ORDINAL_POSITION
            """)
            cols_intento = {r['COLUMN_NAME'] for r in cursor.fetchall()}

            cursor.execute("""
                SELECT intento_id FROM sira.intento_evaluacion 
                WHERE evaluacion_estudiante_id = %s 
                ORDER BY intento_id DESC LIMIT 1
            """, (ee_id,))
            existing = cursor.fetchone()
            if existing:
                intento_id = existing['intento_id'] if isinstance(existing, dict) else existing[0]
            else:
                if 'estado' in cols_intento:
                    try:
                        cursor.execute("""
                            SELECT COLUMN_TYPE FROM information_schema.COLUMNS
                            WHERE TABLE_SCHEMA = DATABASE()
                              AND TABLE_NAME = 'intento_evaluacion'
                              AND COLUMN_NAME = 'estado'
                        """)
                        tipo_col = cursor.fetchone()
                        col_type_str = tipo_col['COLUMN_TYPE'] if isinstance(tipo_col, dict) else tipo_col[0]
                        import re
                        valores = re.findall(r"'([^']+)'", col_type_str)
                        estado_inicial = 'aceptado' if 'aceptado' in valores else (valores[0] if valores else None)
                    except Exception:
                        estado_inicial = None

                    if estado_inicial:
                        cursor.execute("""
                            INSERT INTO sira.intento_evaluacion
                                (evaluacion_estudiante_id, estado)
                            VALUES (%s, %s)
                        """, (ee_id, estado_inicial))
                    else:
                        cursor.execute("""
                            INSERT INTO sira.intento_evaluacion
                                (evaluacion_estudiante_id)
                            VALUES (%s)
                        """, (ee_id,))
                else:
                    cursor.execute("""
                        INSERT INTO sira.intento_evaluacion
                            (evaluacion_estudiante_id)
                        VALUES (%s)
                    """, (ee_id,))
                db.commit()
                intento_id = cursor.lastrowid
        except Exception:
            pass

        for resp in data.respuestas:
            texto_val = resp.texto_respuesta

            try:
                if usa_ee and col_link == 'evaluacion_estudiante_id':
                    cursor.execute(f"""
                        DELETE FROM sira.respuesta_estudiante
                        WHERE evaluacion_estudiante_id = %s AND pregunta_id = %s
                    """, (ee_id, resp.pregunta_id))
                    
                    if resp.opcion_id is not None and intento_id:
                        cursor.execute(f"""
                            INSERT INTO sira.respuesta_estudiante
                                (evaluacion_estudiante_id, pregunta_id, {col_txt}, opcion_id, intento_id)
                            VALUES (%s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE opcion_id=VALUES(opcion_id), {col_txt}=VALUES({col_txt})
                        """, (ee_id, resp.pregunta_id, texto_val, resp.opcion_id, intento_id))
                    elif resp.opcion_id is not None:
                        cursor.execute(f"""
                            INSERT INTO sira.respuesta_estudiante
                                (evaluacion_estudiante_id, pregunta_id, {col_txt}, opcion_id)
                            VALUES (%s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE opcion_id=VALUES(opcion_id), {col_txt}=VALUES({col_txt})
                        """, (ee_id, resp.pregunta_id, texto_val, resp.opcion_id))
                    elif intento_id:
                        cursor.execute(f"""
                            INSERT INTO sira.respuesta_estudiante
                                (evaluacion_estudiante_id, pregunta_id, {col_txt}, intento_id)
                            VALUES (%s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE {col_txt}=VALUES({col_txt}), intento_id=VALUES(intento_id)
                        """, (ee_id, resp.pregunta_id, texto_val, intento_id))
                    else:
                        cursor.execute(f"""
                            INSERT INTO sira.respuesta_estudiante
                                (evaluacion_estudiante_id, pregunta_id, {col_txt})
                            VALUES (%s, %s, %s)
                            ON DUPLICATE KEY UPDATE {col_txt}=VALUES({col_txt})
                        """, (ee_id, resp.pregunta_id, texto_val))

                elif col_link == 'estudiante_id':
                    cursor.execute(f"""
                        DELETE FROM sira.respuesta_estudiante
                        WHERE estudiante_id = %s AND pregunta_id = %s
                    """, (data.estudiante_id, resp.pregunta_id))
                    
                    if resp.opcion_id is not None and intento_id:
                        cursor.execute(f"""
                            INSERT INTO sira.respuesta_estudiante
                                (estudiante_id, pregunta_id, {col_txt}, opcion_id, intento_id)
                            VALUES (%s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE opcion_id=VALUES(opcion_id), {col_txt}=VALUES({col_txt})
                        """, (data.estudiante_id, resp.pregunta_id, texto_val, resp.opcion_id, intento_id))
                    elif resp.opcion_id is not None:
                        cursor.execute(f"""
                            INSERT INTO sira.respuesta_estudiante
                                (estudiante_id, pregunta_id, {col_txt}, opcion_id)
                            VALUES (%s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE opcion_id=VALUES(opcion_id), {col_txt}=VALUES({col_txt})
                        """, (data.estudiante_id, resp.pregunta_id, texto_val, resp.opcion_id))
                    elif intento_id:
                        cursor.execute(f"""
                            INSERT INTO sira.respuesta_estudiante
                                (estudiante_id, pregunta_id, {col_txt}, intento_id)
                            VALUES (%s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE {col_txt}=VALUES({col_txt}), intento_id=VALUES(intento_id)
                        """, (data.estudiante_id, resp.pregunta_id, texto_val, intento_id))
                    else:
                        cursor.execute(f"""
                            INSERT INTO sira.respuesta_estudiante
                                (estudiante_id, pregunta_id, {col_txt})
                            VALUES (%s, %s, %s)
                            ON DUPLICATE KEY UPDATE {col_txt}=VALUES({col_txt})
                        """, (data.estudiante_id, resp.pregunta_id, texto_val))

                else:
                    if resp.opcion_id is not None and intento_id:
                        cursor.execute(f"""
                            INSERT INTO sira.respuesta_estudiante
                                (pregunta_id, {col_txt}, opcion_id, intento_id)
                            VALUES (%s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE opcion_id=VALUES(opcion_id), {col_txt}=VALUES({col_txt})
                        """, (resp.pregunta_id, texto_val, resp.opcion_id, intento_id))
                    elif resp.opcion_id is not None:
                        cursor.execute(f"""
                            INSERT INTO sira.respuesta_estudiante
                                (pregunta_id, {col_txt}, opcion_id)
                            VALUES (%s, %s, %s)
                            ON DUPLICATE KEY UPDATE opcion_id=VALUES(opcion_id), {col_txt}=VALUES({col_txt})
                        """, (resp.pregunta_id, texto_val, resp.opcion_id))
                    elif intento_id:
                        cursor.execute(f"""
                            INSERT INTO sira.respuesta_estudiante
                                (pregunta_id, {col_txt}, intento_id)
                            VALUES (%s, %s, %s)
                            ON DUPLICATE KEY UPDATE {col_txt}=VALUES({col_txt}), intento_id=VALUES(intento_id)
                        """, (resp.pregunta_id, texto_val, intento_id))
                    else:
                        cursor.execute(f"""
                            INSERT INTO sira.respuesta_estudiante
                                (pregunta_id, {col_txt})
                            VALUES (%s, %s)
                            ON DUPLICATE KEY UPDATE {col_txt}=VALUES({col_txt})
                        """, (resp.pregunta_id, texto_val))

            except mysql_errors.Error as col_err:
                if usa_ee:
                    if resp.opcion_id is not None and intento_id:
                        cursor.execute("""
                            INSERT INTO sira.respuesta_estudiante
                                (evaluacion_estudiante_id, pregunta_id, opcion_id, intento_id)
                            VALUES (%s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE opcion_id = VALUES(opcion_id)
                        """, (ee_id, resp.pregunta_id, resp.opcion_id, intento_id))
                    elif resp.opcion_id is not None:
                        cursor.execute("""
                            INSERT INTO sira.respuesta_estudiante
                                (evaluacion_estudiante_id, pregunta_id, opcion_id)
                            VALUES (%s, %s, %s)
                            ON DUPLICATE KEY UPDATE opcion_id = VALUES(opcion_id)
                        """, (ee_id, resp.pregunta_id, resp.opcion_id))
                    elif intento_id:
                        cursor.execute("""
                            INSERT INTO sira.respuesta_estudiante
                                (evaluacion_estudiante_id, pregunta_id, intento_id)
                            VALUES (%s, %s, %s)
                            ON DUPLICATE KEY UPDATE intento_id = VALUES(intento_id)
                        """, (ee_id, resp.pregunta_id, intento_id))
                    else:
                        cursor.execute("""
                            INSERT INTO sira.respuesta_estudiante
                                (evaluacion_estudiante_id, pregunta_id)
                            VALUES (%s, %s)
                            ON DUPLICATE KEY UPDATE evaluacion_estudiante_id = VALUES(evaluacion_estudiante_id)
                        """, (ee_id, resp.pregunta_id))
                else:
                    if resp.opcion_id is not None and intento_id:
                        cursor.execute("""
                            INSERT INTO sira.respuesta_estudiante
                                (pregunta_id, opcion_id, intento_id)
                            VALUES (%s, %s, %s)
                        """, (resp.pregunta_id, resp.opcion_id, intento_id))
                    elif resp.opcion_id is not None:
                        cursor.execute("""
                            INSERT INTO sira.respuesta_estudiante
                                (pregunta_id, opcion_id)
                            VALUES (%s, %s)
                        """, (resp.pregunta_id, resp.opcion_id))
                    elif intento_id:
                        cursor.execute("""
                            INSERT INTO sira.respuesta_estudiante
                                (pregunta_id, intento_id)
                            VALUES (%s, %s)
                        """, (resp.pregunta_id, intento_id))
                    else:
                        cursor.execute("""
                            INSERT INTO sira.respuesta_estudiante
                                (pregunta_id)
                            VALUES (%s)
                        """, (resp.pregunta_id,))

        respuestas_correctas = 0
        total_respuestas     = max(len(data.respuestas), 1)
        try:
            if usa_ee:
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
                    WHERE re.estudiante_id = %s
                """, (data.estudiante_id,))

            cal = cursor.fetchone()
            if cal and cal.get('total'):
                total_respuestas     = int(cal['total'])
                respuestas_correctas = int(cal['correctas'] or 0)
        except Exception:
            pass

        try:
            if intento_id:
                cursor.execute("""
                    UPDATE sira.intento_evaluacion
                    SET respuestas_correctas = %s, estado = 'aceptado'
                    WHERE intento_id = %s
                """, (respuestas_correctas, intento_id))
        except Exception:
            pass

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
            "respuestas_correctas": respuestas_correctas,
            "total": total_respuestas,
            "aprobada": aprobada,
        }

    except mysql_errors.Error as err:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error en BD: {err.msg}")
    except HTTPException:
        db.rollback()
        cursor.close()
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

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

class RetroalimentacionCreate(BaseModel):
    respuesta_id: int
    calificacion_estrellas: int  
    retroalimentacion_maestro: str

class RetroalimentacionUpdate(BaseModel):
    calificacion_estrellas: Optional[int] = None
    retroalimentacion_maestro: Optional[str] = None

class LikeRetroalimentacionCreate(BaseModel):
    liked: bool = True

@router.post("/respuesta/{respuesta_id}/retroalimentacion")
def guardar_retroalimentacion(respuesta_id: int, data: RetroalimentacionCreate, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True) # <--- AQUÍ ESTABA EL ERROR. ¡Asegúrate de poner esto!
    try:
        # Validar que la respuesta existe
        cursor.execute("SELECT respuesta_id FROM sira.respuesta_estudiante WHERE respuesta_id = %s", (respuesta_id,))
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Respuesta no encontrada")

        # Validar rango de estrellas
        if not (1 <= data.calificacion_estrellas <= 5):
            cursor.close()
            raise HTTPException(status_code=400, detail="Estrellas deben estar entre 0 y 5")

        # Actualizar respuesta con retroalimentación
        cursor.execute("""
            UPDATE sira.respuesta_estudiante 
            SET calificacion_estrellas = %s,
                retroalimentacion_maestro = %s,
                fecha_retroalimentacion = NOW(),
                actualizado_en = NOW()
            WHERE respuesta_id = %s
        """, (data.calificacion_estrellas, data.retroalimentacion_maestro, respuesta_id))
        
        db.commit()

        # Retornar respuesta actualizada
        cursor.execute("""
            SELECT respuesta_id, calificacion_estrellas, retroalimentacion_maestro, 
                   fecha_retroalimentacion, creado_en
            FROM sira.respuesta_estudiante 
            WHERE respuesta_id = %s
        """, (respuesta_id,))
        result = cursor.fetchone()
        cursor.close()
        return result
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")

@router.put("/respuesta/{respuesta_id}/retroalimentacion")
def actualizar_retroalimentacion(respuesta_id: int, data: RetroalimentacionUpdate, db=Depends(get_db)):
    cursor = db.cursor()
    try:
        cursor.execute("SELECT respuesta_id FROM sira.respuesta_estudiante WHERE respuesta_id = %s", (respuesta_id,))
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Respuesta no encontrada")

        updates = []
        params = []
        
        if data.calificacion_estrellas is not None:
            if not (1 <= data.calificacion_estrellas <= 5):
                cursor.close()
                raise HTTPException(status_code=400, detail="Estrellas deben estar entre 0 y 5")
            updates.append("calificacion_estrellas = %s")
            params.append(data.calificacion_estrellas)
        
        if data.retroalimentacion_maestro is not None:
            updates.append("retroalimentacion_maestro = %s")
            params.append(data.retroalimentacion_maestro)

        if not updates:
            cursor.close()
            raise HTTPException(status_code=400, detail="Sin datos para actualizar")

        updates.append("actualizado_en = NOW()")
        params.append(respuesta_id)

        query = f"UPDATE sira.respuesta_estudiante SET {', '.join(updates)} WHERE respuesta_id = %s"
        cursor.execute(query, params)
        db.commit()

        cursor.execute("""
            SELECT respuesta_id, calificacion_estrellas, retroalimentacion_maestro, 
                   fecha_retroalimentacion, creado_en
            FROM sira.respuesta_estudiante 
            WHERE respuesta_id = %s
        """, (respuesta_id,))
        result = cursor.fetchone()
        cursor.close()
        return result
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")

@router.post("/respuesta/{respuesta_id}/like-retroalimentacion")
def marcar_like_retroalimentacion(respuesta_id: int, data: LikeRetroalimentacionCreate, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT respuesta_id FROM sira.respuesta_estudiante WHERE respuesta_id = %s",
            (respuesta_id,)
        )
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Respuesta no encontrada")

        cursor.execute("""
            UPDATE sira.respuesta_estudiante
            SET retroalimentacion_like_alumno = %s,
                fecha_like_retroalimentacion = CASE WHEN %s THEN NOW() ELSE NULL END,
                actualizado_en = NOW()
            WHERE respuesta_id = %s
        """, (data.liked, data.liked, respuesta_id))
        db.commit()

        cursor.execute("""
            SELECT respuesta_id, retroalimentacion_like_alumno, fecha_like_retroalimentacion
            FROM sira.respuesta_estudiante
            WHERE respuesta_id = %s
        """, (respuesta_id,))
        result = cursor.fetchone()
        cursor.close()
        return result
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")

@router.get("/respuesta/{respuesta_id}/retroalimentacion")
def obtener_retroalimentacion(respuesta_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT respuesta_id, calificacion_estrellas, retroalimentacion_maestro, 
                   fecha_retroalimentacion, creado_en
            FROM sira.respuesta_estudiante 
            WHERE respuesta_id = %s
        """, (respuesta_id,))
        result = cursor.fetchone()
        cursor.close()
        
        if not result:
            raise HTTPException(status_code=404, detail="Respuesta no encontrada")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/evaluacion/{evaluacion_id}/resumen-retroalimentaciones")
def obtener_resumen_retroalimentaciones(evaluacion_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT 
                e.evaluacion_id,
                e.titulo,
                p.pregunta_id,
                p.texto_pregunta,
                COUNT(r.respuesta_id) as total_respuestas,
                COUNT(CASE WHEN r.calificacion_estrellas IS NOT NULL THEN 1 END) as respuestas_con_retroalimentacion,
                AVG(CASE WHEN r.calificacion_estrellas IS NOT NULL THEN r.calificacion_estrellas END) as promedio_estrellas,
                GROUP_CONCAT(
                    JSON_OBJECT(
                        'respuesta_id', r.respuesta_id,
                        'estrellas', r.calificacion_estrellas,
                        'retroalimentacion', r.retroalimentacion_maestro,
                        'fecha', r.fecha_retroalimentacion
                    )
                ) as retroalimentaciones
            FROM sira.evaluacion e
            JOIN sira.pregunta p ON e.evaluacion_id = p.evaluacion_id
            LEFT JOIN sira.respuesta_estudiante r ON p.pregunta_id = r.pregunta_id
            WHERE e.evaluacion_id = %s
            GROUP BY e.evaluacion_id, p.pregunta_id
            ORDER BY p.orden
        """, (evaluacion_id,))
        
        result = cursor.fetchall()
        cursor.close()
        
        if not result:
            raise HTTPException(status_code=404, detail="Evaluación no encontrada")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")