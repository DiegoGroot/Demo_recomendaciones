from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from database import get_db
from mysql.connector import errors as mysql_errors
from utils import generar_recomendaciones_por_calificacion

router = APIRouter()

class RecomendacionCreate(BaseModel):
    estudiante_id: int
    materia_id: Optional[int] = None
    tipo_recomendacion: str
    descripcion: str
    prioridad: str = "media"
    enlace_archivo: Optional[str] = None 
    fecha_limite: Optional[str] = None 
    retroalimentacion_docente: Optional[str] = None

class RecomendacionUpdate(BaseModel):
    tipo_recomendacion: Optional[str] = None
    descripcion: Optional[str] = None
    prioridad: Optional[str] = None
    estado: Optional[str] = None
    enlace_archivo: Optional[str] = None 
    fecha_limite: Optional[str] = None
    estrellas_docente: Optional[int] = None
    retroalimentacion_docente: Optional[str] = None

@router.get("")
def listar_recomendaciones(
    estudiante_id: Optional[int] = Query(None),
    prioridad: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    db=Depends(get_db),
):
    cursor = db.cursor(dictionary=True)
    try:
        query = """
            SELECT r.recomendacion_id, r.estudiante_id, e.nombre as estudiante_nombre,
                   r.materia_id, m.nombre as materia_nombre, r.tipo_recomendacion, r.descripcion,
                   r.prioridad, r.estado, r.fecha_creacion, r.fecha_actualizacion,
                   r.enlace_archivo, r.fecha_limite, r.estrellas_docente, r.retroalimentacion_docente
            FROM sira.recomendacion r
            LEFT JOIN sira.estudiante e ON r.estudiante_id = e.estudiante_id
            LEFT JOIN sira.materia m ON r.materia_id = m.materia_id
            WHERE 1=1
        """
        params = []
        if estudiante_id:
            query += " AND r.estudiante_id = %s"
            params.append(estudiante_id)
        if prioridad:
            query += " AND r.prioridad = %s"
            params.append(prioridad)
            
        # Filtro inteligente a prueba de errores de Flutter
        if estado:
            estado_lower = estado.lower()
            if estado_lower == 'todas':
                pass # No filtramos, trae todas
            else:
                if estado_lower == 'activas': estado_lower = 'activa'
                if estado_lower == 'resueltas': estado_lower = 'resuelta'
                query += " AND r.estado = %s"
                params.append(estado_lower)

        query += " ORDER BY r.fecha_creacion DESC"
        cursor.execute(query, params) if params else cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        
        # Convertir fechas a string seguro
        for row in result:
            for key in ['fecha_creacion', 'fecha_actualizacion', 'fecha_limite']:
                if row.get(key):
                    row[key] = str(row[key])
                
        return result if result else []
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error BD: {str(e)}")

@router.post("", status_code=201)
def crear_recomendacion(data: RecomendacionCreate, db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT estudiante_id FROM sira.estudiante WHERE estudiante_id = %s", (data.estudiante_id,))
    if not cursor.fetchone():
        cursor.close()
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    try:
        cursor.execute(
            """
            INSERT INTO sira.recomendacion 
            (estudiante_id, materia_id, tipo_recomendacion, descripcion, prioridad, estado, enlace_archivo, fecha_limite, retroalimentacion_docente)
            VALUES (%s, %s, %s, %s, %s, 'activa', %s, %s, %s)
            """,
            (data.estudiante_id, data.materia_id, data.tipo_recomendacion, data.descripcion, data.prioridad, data.enlace_archivo, data.fecha_limite, data.retroalimentacion_docente),
        )
        db.commit()
        cursor.execute("SELECT * FROM sira.recomendacion WHERE recomendacion_id = LAST_INSERT_ID()")
        result = cursor.fetchone()
        cursor.close()
        return {"mensaje": "Recomendacion creada"}
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{recomendacion_id}")
def actualizar_recomendacion(recomendacion_id: int, data: RecomendacionUpdate, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT recomendacion_id FROM sira.recomendacion WHERE recomendacion_id = %s", (recomendacion_id,))
    if not cursor.fetchone():
        cursor.close()
        raise HTTPException(status_code=404, detail="Recomendación no encontrada")

    campos = {k: v for k, v in data.model_dump().items() if v is not None}
    if not campos:
        cursor.close()
        raise HTTPException(status_code=400, detail="No hay campos para actualizar")

    set_clause = ", ".join([f"{k} = %s" for k in campos])
    try:
        cursor.execute(f"UPDATE sira.recomendacion SET {set_clause} WHERE recomendacion_id = %s", (*campos.values(), recomendacion_id))
        db.commit()
        cursor.close()
        return {"mensaje": "Recomendación actualizada"}
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{recomendacion_id}")
def eliminar_recomendacion(recomendacion_id: int, db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT recomendacion_id FROM sira.recomendacion WHERE recomendacion_id = %s", (recomendacion_id,))
    if not cursor.fetchone():
        cursor.close()
        raise HTTPException(status_code=404, detail="Recomendación no encontrada")
    try:
        cursor.execute("DELETE FROM sira.recomendacion WHERE recomendacion_id = %s", (recomendacion_id,))
        db.commit()
        cursor.close()
        return {"mensaje": "Recomendación eliminada"}
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/generar/por-calificacion/{calificacion_id}")
def generar_recomendacion_por_calificacion(calificacion_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT c.calificacion_id, c.estudiante_id, c.materia_id, c.nota_final, c.estado
            FROM sira.calificacion c
            WHERE c.calificacion_id = %s
        """, (calificacion_id,))
        cal = cursor.fetchone()
        
        if not cal:
            cursor.close()
            raise HTTPException(status_code=404, detail="Calificación no encontrada")
        if cal['estado'] == 'en_curso':
            cursor.close()
            raise HTTPException(status_code=400, detail="La calificación debe estar finalizada")
        
        rec_data = generar_recomendaciones_por_calificacion(
            cal['nota_final'], cal['estudiante_id'], cal['materia_id']
        )
        
        cursor.execute("""
            SELECT recomendacion_id FROM sira.recomendacion
            WHERE estudiante_id = %s AND materia_id = %s AND estado = 'activa'
        """, (cal['estudiante_id'], cal['materia_id']))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute("""
                UPDATE sira.recomendacion
                SET tipo_recomendacion = %s, descripcion = %s, prioridad = %s
                WHERE recomendacion_id = %s
            """, (rec_data['tipo_recomendacion'], rec_data['descripcion'],
                  rec_data['prioridad'], existing['recomendacion_id']))
            db.commit()
            rec_id = existing['recomendacion_id']
        else:
            cursor.execute("""
                INSERT INTO sira.recomendacion
                (estudiante_id, materia_id, tipo_recomendacion, descripcion, prioridad, estado, fuente)
                VALUES (%s, %s, %s, %s, %s, 'activa', 'automatica')
            """, (rec_data['estudiante_id'], rec_data['materia_id'],
                  rec_data['tipo_recomendacion'], rec_data['descripcion'],
                  rec_data['prioridad']))
            db.commit()
            rec_id = cursor.lastrowid
        
        cursor.execute("""
            SELECT r.recomendacion_id, r.estudiante_id, e.nombre as estudiante_nombre,
                   r.materia_id, m.nombre as materia_nombre, r.tipo_recomendacion, r.descripcion,
                   r.prioridad, r.estado, r.fecha_creacion, r.fecha_actualizacion, r.fuente
            FROM sira.recomendacion r
            JOIN sira.estudiante e ON r.estudiante_id = e.estudiante_id
            LEFT JOIN sira.materia m ON r.materia_id = m.materia_id
            WHERE r.recomendacion_id = %s
        """, (rec_id,))
        resultado = cursor.fetchone()
        cursor.close()
        return resultado
    except HTTPException:
        cursor.close()
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.post("/{recomendacion_id}/calificar")
def calificar_recomendacion(recomendacion_id: int, body: dict, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT recomendacion_id FROM sira.recomendacion WHERE recomendacion_id = %s", (recomendacion_id,))
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Recomendación no encontrada")
        
        # Extraemos las estrellas y el comentario
        estrellas = body.get('estrellas_docente', body.get('calificacion', 0))
        retro = body.get('retroalimentacion_docente', '')
        
        # Guardamos en la base de datos
        cursor.execute(
            """UPDATE sira.recomendacion SET estado = 'resuelta', 
               estrellas_docente = %s, retroalimentacion_docente = %s 
               WHERE recomendacion_id = %s""",
            (estrellas, retro, recomendacion_id),
        )
        db.commit()
        cursor.close()
        return {"mensaje": "Recomendación calificada", "recomendacion_id": recomendacion_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/crear-con-evaluacion", status_code=201)
def crear_recomendacion_con_evaluacion(data: RecomendacionCreate, db=Depends(get_db)):
    """Crea una recomendación y automáticamente genera una evaluación de 5 preguntas"""
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT nombre FROM sira.estudiante WHERE estudiante_id = %s", (data.estudiante_id,))
        est = cursor.fetchone()
        if not est:
            cursor.close()
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")

        if data.materia_id:
            cursor.execute("SELECT nombre FROM sira.materia WHERE materia_id = %s", (data.materia_id,))
            mat = cursor.fetchone()
            materia_nombre = mat['nombre'] if mat else "la materia"
        else:
            materia_nombre = "sus estudios"

        # Insertar recomendación incluyendo el enlace y fecha limite
        cursor.execute(
            """INSERT INTO sira.recomendacion
               (estudiante_id, materia_id, tipo_recomendacion, descripcion, prioridad, estado, fuente, enlace_archivo, fecha_limite, retroalimentacion_docente)
               VALUES (%s, %s, %s, %s, %s, 'activa', 'manual', %s, %s, %s)""",
            (data.estudiante_id, data.materia_id, data.tipo_recomendacion,
             data.descripcion, data.prioridad, data.enlace_archivo, data.fecha_limite, data.retroalimentacion_docente)
        )
        db.commit()
        rec_id = cursor.lastrowid

        preguntas_por_tipo = {
            "mejora_academica": [
                ("¿Cuántas horas diarias dedicas actualmente al estudio?",
                 [("Menos de 1 hora", False), ("1-2 horas", False), ("2-4 horas", True), ("Más de 4 horas", True)]),
                ("¿Utilizas técnicas de estudio estructuradas?",
                 [("No, estudio sin método", False), ("A veces", False), ("Sí, siempre", True), ("Tengo mi propio método efectivo", True)]),
                (f"¿Entiendes los conceptos fundamentales de {materia_nombre}?",
                 [("No los entiendo", False), ("Entiendo poco", False), ("Los entiendo en su mayoría", True), ("Los domino completamente", True)]),
                ("¿Buscas ayuda cuando tienes dudas académicas?",
                 [("Nunca", False), ("Rara vez", False), ("Con frecuencia", True), ("Siempre que la necesito", True)]),
                ("¿Con qué frecuencia repasas el material de clase?",
                 [("Nunca", False), ("Solo antes de exámenes", False), ("Semanalmente", True), ("Diariamente", True)]),
            ],
            "tutoria": [
                ("¿Asistes regularmente a las sesiones de tutoría disponibles?",
                 [("Nunca he asistido", False), ("Pocas veces", False), ("La mayoría de sesiones", True), ("Siempre asisto", True)]),
                ("¿Identificas claramente cuáles son tus áreas de dificultad?",
                 [("No tengo claridad", False), ("Tengo algunas ideas", False), ("Las identifico bien", True), ("Las tengo muy claras", True)]),
                (f"¿Has pedido apoyo a tu maestro sobre {materia_nombre}?",
                 [("Nunca", False), ("Solo una vez", False), ("Algunas veces", True), ("Con frecuencia", True)]),
                ("¿Trabajas en grupo con tus compañeros para estudiar?",
                 [("Nunca", False), ("Rara vez", False), ("Frecuentemente", True), ("Siempre", True)]),
                ("¿Preparas preguntas específicas antes de ir a tutoría?",
                 [("No, voy sin preparación", False), ("A veces", False), ("Casi siempre", True), ("Siempre me preparo", True)]),
            ],
            "recuperacion": [
                (f"¿Sabes exactamente qué temas de {materia_nombre} necesitas recuperar?",
                 [("No tengo idea", False), ("Tengo una idea vaga", False), ("Los identifico bien", True), ("Los tengo muy claros", True)]),
                ("¿Has revisado los exámenes o trabajos reprobados para entender tus errores?",
                 [("No los he revisado", False), ("Los revisé superficialmente", False), ("Los analicé con detalle", True), ("Los analicé y busqué soluciones", True)]),
                ("¿Tienes un plan de acción para mejorar tu rendimiento?",
                 [("No tengo ningún plan", False), ("Tengo ideas generales", False), ("Tengo un plan básico", True), ("Tengo un plan detallado", True)]),
                ("¿Qué tan motivado(a) estás para mejorar tu situación académica?",
                 [("Muy poco motivado", False), ("Algo motivado", False), ("Bastante motivado", True), ("Muy motivado y comprometido", True)]),
                ("¿Comunicas tus dificultades académicas a tus tutores o familia?",
                 [("Nunca", False), ("Rara vez", False), ("Con frecuencia", True), ("Siempre busco apoyo", True)]),
            ],
            "orientacion": [
                ("¿Tienes claro tu objetivo académico y profesional a futuro?",
                 [("No tengo claridad", False), ("Tengo ideas vagas", False), ("Lo tengo bastante claro", True), ("Lo tengo muy definido", True)]),
                ("¿Conoces los recursos académicos disponibles en tu institución?",
                 [("No conozco ninguno", False), ("Conozco pocos", False), ("Conozco los principales", True), ("Los conozco todos", True)]),
                ("¿Participas en actividades extracurriculares relacionadas con tu carrera?",
                 [("Nunca", False), ("Rara vez", False), ("Con frecuencia", True), ("Activamente", True)]),
                ("¿Tienes hábitos de vida saludable que apoyen tu rendimiento académico?",
                 [("No los tengo", False), ("Algunos hábitos", False), ("Buenos hábitos generales", True), ("Excelentes hábitos", True)]),
                ("¿Manejas adecuadamente el estrés académico?",
                 [("No, me afecta mucho", False), ("A veces lo manejo", False), ("Generalmente lo controlo", True), ("Lo manejo muy bien", True)]),
            ],
        }

        tipo_key = data.tipo_recomendacion.lower().replace(" ", "_").replace("é", "e").replace("ó", "o")
        preguntas = preguntas_por_tipo.get(tipo_key, preguntas_por_tipo.get("mejora_academica"))

        titulo = f"Evaluación: {data.tipo_recomendacion.replace('_', ' ').title()} — {est['nombre']}"
        cursor.execute(
            "INSERT INTO sira.evaluacion (recomendacion_id, titulo, descripcion) VALUES (%s, %s, %s)",
            (rec_id, titulo, f"Evaluación de seguimiento para la recomendación.")
        )
        db.commit()
        eval_id = cursor.lastrowid

        for i, (texto, opciones) in enumerate(preguntas, 1):
            cursor.execute(
                """INSERT INTO sira.pregunta
                   (evaluacion_id, texto_pregunta, tipo_pregunta, orden, requerida)
                   VALUES (%s, %s, 'opcion_multiple', %s, 1)""",
                (eval_id, texto, i)
            )
            db.commit()
            preg_id = cursor.lastrowid
            for j, (texto_op, es_correcta) in enumerate(opciones, 1):
                cursor.execute(
                    """INSERT INTO sira.opcion_respuesta
                       (pregunta_id, texto_opcion, es_correcta, orden)
                       VALUES (%s, %s, %s, %s)""",
                    (preg_id, texto_op, es_correcta, j)
                )
        db.commit()

        cursor.execute(
            """SELECT r.recomendacion_id, r.estudiante_id, e.nombre as estudiante_nombre,
                      r.materia_id, m.nombre as materia_nombre, r.tipo_recomendacion,
                      r.descripcion, r.prioridad, r.estado, r.fecha_creacion,
                      r.enlace_archivo, r.fecha_limite
               FROM sira.recomendacion r
               JOIN sira.estudiante e ON r.estudiante_id = e.estudiante_id
               LEFT JOIN sira.materia m ON r.materia_id = m.materia_id
               WHERE r.recomendacion_id = %s""",
            (rec_id,)
        )
        rec = cursor.fetchone()
        cursor.close()
        return {**rec, "evaluacion_id": eval_id, "preguntas_generadas": len(preguntas)}

    except HTTPException:
        db.rollback()
        cursor.close()
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/reportes/general")
def obtener_reporte_general_recomendaciones(db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT
                e.estudiante_id,
                e.nombre AS estudiante_nombre,
                c.nombre AS carrera_nombre,
                r.recomendacion_id,
                r.tipo_recomendacion,
                r.descripcion AS recomendacion_descripcion,
                r.prioridad,
                r.estado AS recomendacion_estado,
                r.estrellas_docente,
                r.retroalimentacion_docente,
                m.nombre AS materia_nombre,
                ev.evaluacion_id,
                ev.titulo AS evaluacion_titulo,
                ee.estado AS evaluacion_estado,
                ee.fecha_fin,
                ie.respuestas_correctas
            FROM sira.estudiante e
            LEFT JOIN sira.carrera c ON e.carrera_id = c.carrera_id
            LEFT JOIN sira.recomendacion r ON r.estudiante_id = e.estudiante_id
            LEFT JOIN sira.materia m ON r.materia_id = m.materia_id
            LEFT JOIN sira.evaluacion ev ON ev.recomendacion_id = r.recomendacion_id
            LEFT JOIN sira.seguimiento_recomendacion sr
                   ON sr.recomendacion_id = r.recomendacion_id
                  AND sr.estudiante_id = e.estudiante_id
            LEFT JOIN sira.evaluacion_estudiante ee
                   ON ee.evaluacion_id = ev.evaluacion_id
                  AND ee.seguimiento_id = sr.seguimiento_id
            LEFT JOIN sira.intento_evaluacion ie
                   ON ie.evaluacion_estudiante_id = ee.evaluacion_estudiante_id
            ORDER BY e.nombre, r.fecha_creacion DESC, ev.creado_en DESC
        """)
        rows = cursor.fetchall()

        for row in rows:
            evaluacion_id = row.get('evaluacion_id')
            estudiante_id = row.get('estudiante_id')
            row['respuestas'] = []
            if evaluacion_id and estudiante_id:
                cursor.execute("""
                    SELECT
                        p.orden,
                        p.texto_pregunta,
                        p.tipo_pregunta,
                        COALESCE(NULLIF(re.respuesta_texto, ''), o.texto_opcion, '') AS respuesta_alumno,
                        o.texto_opcion,
                        re.es_correcta,
                        re.retroalimentacion_maestro,
                        re.fecha_retroalimentacion
                    FROM sira.respuesta_estudiante re
                    JOIN sira.intento_evaluacion ie ON re.intento_id = ie.intento_id
                    JOIN sira.evaluacion_estudiante ee ON ie.evaluacion_estudiante_id = ee.evaluacion_estudiante_id
                    JOIN sira.seguimiento_recomendacion sr ON ee.seguimiento_id = sr.seguimiento_id
                    JOIN sira.pregunta p ON re.pregunta_id = p.pregunta_id
                    LEFT JOIN sira.opcion_respuesta o ON re.opcion_id = o.opcion_id
                    WHERE ee.evaluacion_id = %s
                      AND sr.estudiante_id = %s
                    ORDER BY p.orden, re.respuesta_id
                """, (evaluacion_id, estudiante_id))
                row['respuestas'] = cursor.fetchall()

            for key in list(row.keys()):
                if row[key] is not None and 'fecha' in key:
                    row[key] = str(row[key])

        cursor.close()
        return rows if rows else []
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error reporte general: {str(e)}")

@router.get("/{recomendacion_id}/resumen")
def obtener_resumen_recomendacion(recomendacion_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT
                r.recomendacion_id,
                r.estudiante_id,
                e.nombre AS estudiante_nombre,
                e.carrera_id,
                c.nombre AS carrera_nombre,
                r.materia_id,
                m.nombre AS materia_nombre,
                r.tipo_recomendacion,
                r.descripcion,
                r.prioridad,
                r.estado,
                r.estrellas_docente,
                r.retroalimentacion_docente,
                r.enlace_archivo,
                r.fecha_limite,
                r.fecha_creacion,
                r.fecha_actualizacion
            FROM sira.recomendacion r
            JOIN sira.estudiante e ON r.estudiante_id = e.estudiante_id
            LEFT JOIN sira.carrera c ON e.carrera_id = c.carrera_id
            LEFT JOIN sira.materia m ON r.materia_id = m.materia_id
            WHERE r.recomendacion_id = %s
        """, (recomendacion_id,))
        rec = cursor.fetchone()
        if not rec:
            cursor.close()
            raise HTTPException(status_code=404, detail="Recomendación no encontrada")

        cursor.execute("""
            SELECT
                ev.evaluacion_id,
                ev.titulo,
                ev.descripcion,
                ev.estado,
                ev.creado_en,
                ee.evaluacion_estudiante_id,
                ee.estado AS estado_estudiante,
                ee.fecha_inicio,
                ee.fecha_fin,
                ee.evaluacion_aprobada,
                ie.intento_id,
                ie.respuestas_correctas
            FROM sira.evaluacion ev
            LEFT JOIN sira.seguimiento_recomendacion sr
                   ON sr.recomendacion_id = ev.recomendacion_id
                  AND sr.estudiante_id = %s
            LEFT JOIN sira.evaluacion_estudiante ee
                   ON ee.evaluacion_id = ev.evaluacion_id
                  AND ee.seguimiento_id = sr.seguimiento_id
            LEFT JOIN sira.intento_evaluacion ie
                   ON ie.evaluacion_estudiante_id = ee.evaluacion_estudiante_id
            WHERE ev.recomendacion_id = %s
            ORDER BY ev.creado_en DESC, ie.intento_id DESC
        """, (rec['estudiante_id'], recomendacion_id))
        evaluaciones = cursor.fetchall()

        evaluaciones_con_respuestas = []
        for ev in evaluaciones:
            cursor.execute("""
                SELECT
                    re.respuesta_id,
                    p.pregunta_id,
                    p.orden,
                    p.texto_pregunta,
                    p.tipo_pregunta,
                    re.opcion_id,
                    o.texto_opcion,
                    COALESCE(NULLIF(re.respuesta_texto, ''), o.texto_opcion, '') AS respuesta_alumno,
                    re.es_correcta,
                    re.retroalimentacion_maestro,
                    re.fecha_retroalimentacion,
                    re.creado_en
                FROM sira.respuesta_estudiante re
                JOIN sira.intento_evaluacion ie ON re.intento_id = ie.intento_id
                JOIN sira.evaluacion_estudiante ee ON ie.evaluacion_estudiante_id = ee.evaluacion_estudiante_id
                JOIN sira.pregunta p ON re.pregunta_id = p.pregunta_id
                LEFT JOIN sira.opcion_respuesta o ON re.opcion_id = o.opcion_id
                WHERE ee.evaluacion_id = %s
                  AND ee.seguimiento_id IN (
                      SELECT seguimiento_id
                      FROM sira.seguimiento_recomendacion
                      WHERE recomendacion_id = %s
                        AND estudiante_id = %s
                  )
                ORDER BY p.orden, re.respuesta_id
            """, (ev['evaluacion_id'], recomendacion_id, rec['estudiante_id']))
            respuestas = cursor.fetchall()

            ev['respuestas'] = respuestas
            ev['total_respuestas'] = len(respuestas)
            ev['con_retroalimentacion'] = sum(
                1 for r in respuestas if r.get('retroalimentacion_maestro')
            )
            evaluaciones_con_respuestas.append(ev)

        for key in ['fecha_creacion', 'fecha_actualizacion']:
            if rec.get(key):
                rec[key] = str(rec[key])
        for ev in evaluaciones_con_respuestas:
            for key in ['creado_en', 'fecha_inicio', 'fecha_fin']:
                if ev.get(key):
                    ev[key] = str(ev[key])
            for resp in ev.get('respuestas', []):
                for key in ['fecha_retroalimentacion', 'creado_en']:
                    if resp.get(key):
                        resp[key] = str(resp[key])

        cursor.close()
        return {**rec, 'evaluaciones': evaluaciones_con_respuestas}
    except HTTPException:
        raise
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/estudiante/{estudiante_id}/resumen-todos")
def obtener_resumen_recomendaciones_estudiante(estudiante_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT estudiante_id FROM sira.estudiante WHERE estudiante_id = %s", (estudiante_id,))
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")
        cursor.execute("""
            SELECT r.recomendacion_id, r.estudiante_id, r.materia_id, r.tipo_recomendacion, r.descripcion, 
                   r.prioridad, r.estado, r.fecha_creacion, r.estrellas_docente,
                   r.retroalimentacion_docente, r.enlace_archivo, r.fecha_limite,
                   m.nombre as materia_nombre,
                   COUNT(e.evaluacion_id) as total_evaluaciones
            FROM sira.recomendacion r
            LEFT JOIN sira.materia m ON r.materia_id = m.materia_id
            LEFT JOIN sira.evaluacion e ON r.recomendacion_id = e.recomendacion_id
            WHERE r.estudiante_id = %s
            GROUP BY r.recomendacion_id
            ORDER BY r.prioridad DESC, r.fecha_creacion DESC
        """, (estudiante_id,))
        recomendaciones = cursor.fetchall()
        
        stats = {'total': len(recomendaciones), 'por_estado': {}, 'por_prioridad': {}}
        for rec in recomendaciones:
            estado = rec['estado']
            stats['por_estado'][estado] = stats['por_estado'].get(estado, 0) + 1
            prioridad = rec['prioridad']
            stats['por_prioridad'][prioridad] = stats['por_prioridad'].get(prioridad, 0) + 1
        
        cursor.close()
        return {'estudiante_id': estudiante_id, 'recomendaciones': recomendaciones, 'estadisticas': stats}
    except HTTPException:
        raise
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")