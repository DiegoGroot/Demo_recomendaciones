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
    evaluacion_estudiante_id: int
    pregunta_id: int
    texto_respuesta: Optional[str] = None
    opcion_id: Optional[int] = None


class SubmitEvaluacionCreate(BaseModel):
    evaluacion_id: int
    estudiante_id: int
    respuestas: List[RespuestaEstudianteCreate]


# =============== EVALUACIONES ===============

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

        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        result = cursor.fetchall()
        cursor.close()
        return result
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ─── GET evaluaciones pendientes de un estudiante ───────────────────────────
@router.get("/estudiante/{estudiante_id}")
def evaluaciones_por_estudiante(estudiante_id: int, db=Depends(get_db)):
    """
    Devuelve todas las evaluaciones activas asociadas a recomendaciones
    del estudiante que aún NO ha respondido.
    """
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT e.evaluacion_id, e.recomendacion_id, e.titulo, e.descripcion,
                   e.estado, e.creado_en,
                   r.tipo_recomendacion, r.prioridad,
                   (
                     SELECT COUNT(*) FROM sira.evaluacion_estudiante ee
                     WHERE ee.evaluacion_id = e.evaluacion_id
                       AND ee.estudiante_id = %s
                       AND ee.completada = 1
                   ) as ya_respondida
            FROM sira.evaluacion e
            JOIN sira.recomendacion r ON e.recomendacion_id = r.recomendacion_id
            WHERE r.estudiante_id = %s
              AND e.estado = 'activa'
            ORDER BY e.creado_en DESC
        """, (estudiante_id, estudiante_id))
        result = cursor.fetchall()
        cursor.close()
        # Convertir bit/int a bool
        for row in result:
            row['ya_respondida'] = bool(row.get('ya_respondida', 0))
        return result if result else []
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/{evaluacion_id}")
def obtener_evaluacion(evaluacion_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT e.evaluacion_id, e.recomendacion_id, e.titulo, e.descripcion,
                   e.estado, e.creado_en
            FROM sira.evaluacion e
            WHERE e.evaluacion_id = %s
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


@router.post("", status_code=201)
def crear_evaluacion(data: EvaluacionCreate, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT recomendacion_id FROM sira.recomendacion WHERE recomendacion_id = %s",
                      (data.recomendacion_id,))
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


@router.put("/{evaluacion_id}")
def actualizar_evaluacion(evaluacion_id: int, data: EvaluacionUpdate, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT evaluacion_id FROM sira.evaluacion WHERE evaluacion_id = %s", (evaluacion_id,))
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Evaluación no encontrada")

        campos = {k: v for k, v in data.dict().items() if v is not None}
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
        cursor.execute("SELECT evaluacion_id FROM sira.evaluacion WHERE evaluacion_id = %s", (evaluacion_id,))
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


# =============== PREGUNTAS ===============

@router.get("/preguntas/evaluacion/{evaluacion_id}")
def preguntas_por_evaluacion(evaluacion_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        # Preguntas
        cursor.execute("""
            SELECT p.pregunta_id, p.evaluacion_id, p.texto_pregunta,
                   p.tipo_pregunta, p.orden, p.requerida, p.creado_en
            FROM sira.pregunta p
            WHERE p.evaluacion_id = %s
            ORDER BY p.orden
        """, (evaluacion_id,))
        preguntas = cursor.fetchall()

        # Para cada pregunta con opciones, cargarlas
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
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/preguntas", status_code=201)
def crear_pregunta(data: PreguntaCreate, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT evaluacion_id FROM sira.evaluacion WHERE evaluacion_id = %s",
                      (data.evaluacion_id,))
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Evaluación no encontrada")

        cursor.execute("""
            INSERT INTO sira.pregunta (evaluacion_id, texto_pregunta, tipo_pregunta, orden, requerida)
            VALUES (%s, %s, %s, %s, %s)
        """, (data.evaluacion_id, data.texto_pregunta, data.tipo_pregunta, data.orden, data.requerida))
        db.commit()
        new_id = cursor.lastrowid

        cursor.execute("""
            SELECT pregunta_id, evaluacion_id, texto_pregunta, tipo_pregunta, orden, requerida, creado_en
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
        cursor.execute("SELECT pregunta_id FROM sira.pregunta WHERE pregunta_id = %s", (pregunta_id,))
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Pregunta no encontrada")

        campos = {k: v for k, v in data.dict().items() if v is not None}
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
            SELECT pregunta_id, evaluacion_id, texto_pregunta, tipo_pregunta, orden, requerida, creado_en
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
        cursor.execute("SELECT pregunta_id FROM sira.pregunta WHERE pregunta_id = %s", (pregunta_id,))
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


# =============== OPCIONES DE RESPUESTA ===============

@router.get("/opciones/pregunta/{pregunta_id}")
def opciones_por_pregunta(pregunta_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT o.opcion_id, o.pregunta_id, o.texto_opcion,
                   o.es_correcta, o.orden, o.creado_en
            FROM sira.opcion_respuesta o
            WHERE o.pregunta_id = %s
            ORDER BY o.orden
        """, (pregunta_id,))
        result = cursor.fetchall()
        cursor.close()
        return result if result else []
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
            FROM sira.opcion_respuesta o
            WHERE o.opcion_id = %s
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
        cursor.execute("SELECT pregunta_id FROM sira.pregunta WHERE pregunta_id = %s",
                      (data.pregunta_id,))
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
        cursor.execute("SELECT opcion_id FROM sira.opcion_respuesta WHERE opcion_id = %s", (opcion_id,))
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Opción no encontrada")

        campos = {k: v for k, v in data.dict().items() if v is not None}
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
        cursor.execute("SELECT opcion_id FROM sira.opcion_respuesta WHERE opcion_id = %s", (opcion_id,))
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


# =============== RESPUESTAS DEL ESTUDIANTE ===============

@router.post("/iniciar", status_code=201)
def iniciar_evaluacion(data: IniciarEvaluacionCreate, db=Depends(get_db)):
    """
    Crea un registro evaluacion_estudiante para rastrear el intento.
    Si ya existe uno incompleto, lo devuelve.
    """
    cursor = db.cursor(dictionary=True)
    try:
        # Verificar si ya existe uno en curso
        cursor.execute("""
            SELECT ee_id, evaluacion_id, estudiante_id, completada, iniciado_en
            FROM sira.evaluacion_estudiante
            WHERE evaluacion_id = %s AND estudiante_id = %s AND completada = 0
        """, (data.evaluacion_id, data.estudiante_id))
        existente = cursor.fetchone()
        if existente:
            cursor.close()
            return existente

        cursor.execute("""
            INSERT INTO sira.evaluacion_estudiante (evaluacion_id, estudiante_id, completada)
            VALUES (%s, %s, 0)
        """, (data.evaluacion_id, data.estudiante_id))
        db.commit()
        new_id = cursor.lastrowid

        cursor.execute("""
            SELECT ee_id, evaluacion_id, estudiante_id, completada, iniciado_en
            FROM sira.evaluacion_estudiante WHERE ee_id = %s
        """, (new_id,))
        result = cursor.fetchone()
        cursor.close()
        return result
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/respuestas/submit", status_code=201)
def submit_respuestas(data: SubmitEvaluacionCreate, db=Depends(get_db)):
    """
    Guarda todas las respuestas de un estudiante y marca la evaluación como completada.
    """
    cursor = db.cursor(dictionary=True)
    try:
        # Buscar o crear el registro evaluacion_estudiante
        cursor.execute("""
            SELECT ee_id FROM sira.evaluacion_estudiante
            WHERE evaluacion_id = %s AND estudiante_id = %s
        """, (data.evaluacion_id, data.estudiante_id))
        ee = cursor.fetchone()

        if not ee:
            cursor.execute("""
                INSERT INTO sira.evaluacion_estudiante (evaluacion_id, estudiante_id, completada)
                VALUES (%s, %s, 0)
            """, (data.evaluacion_id, data.estudiante_id))
            db.commit()
            ee_id = cursor.lastrowid
        else:
            ee_id = ee['ee_id']

        # Insertar cada respuesta
        for resp in data.respuestas:
            # Evitar duplicados: borrar respuesta previa si existe
            cursor.execute("""
                DELETE FROM sira.respuesta_estudiante
                WHERE evaluacion_estudiante_id = %s AND pregunta_id = %s
            """, (ee_id, resp.pregunta_id))

            cursor.execute("""
                INSERT INTO sira.respuesta_estudiante
                (evaluacion_estudiante_id, pregunta_id, texto_respuesta, opcion_id)
                VALUES (%s, %s, %s, %s)
            """, (ee_id, resp.pregunta_id, resp.texto_respuesta, resp.opcion_id))

        # Calcular calificación automática (preguntas con opcion correcta)
        cursor.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN o.es_correcta = 1 THEN 1 ELSE 0 END) as correctas
            FROM sira.respuesta_estudiante re
            JOIN sira.opcion_respuesta o ON re.opcion_id = o.opcion_id
            WHERE re.evaluacion_estudiante_id = %s
        """, (ee_id,))
        cal = cursor.fetchone()
        calificacion = None
        if cal and cal['total'] and cal['total'] > 0:
            calificacion = round((cal['correctas'] / cal['total']) * 10, 2)

        # Marcar como completada
        cursor.execute("""
            UPDATE sira.evaluacion_estudiante
            SET completada = 1, calificacion = %s, completado_en = NOW()
            WHERE ee_id = %s
        """, (calificacion, ee_id))
        db.commit()

        cursor.close()
        return {
            "message": "Respuestas enviadas correctamente",
            "ee_id": ee_id,
            "calificacion": calificacion
        }
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/resultados/estudiante/{estudiante_id}")
def resultados_por_estudiante(estudiante_id: int, db=Depends(get_db)):
    """
    Devuelve los resultados de todas las evaluaciones completadas del estudiante.
    """
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT ee.ee_id, ee.evaluacion_id, ee.calificacion,
                   ee.completada, ee.iniciado_en, ee.completado_en,
                   ev.titulo, ev.descripcion
            FROM sira.evaluacion_estudiante ee
            JOIN sira.evaluacion ev ON ee.evaluacion_id = ev.evaluacion_id
            WHERE ee.estudiante_id = %s AND ee.completada = 1
            ORDER BY ee.completado_en DESC
        """, (estudiante_id,))
        result = cursor.fetchall()
        cursor.close()
        return result if result else []
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")