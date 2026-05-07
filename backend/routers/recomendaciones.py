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
    tipo_recomendacion: str  # mejora_academica, tutoria, recuperacion, orientacion
    descripcion: str
    prioridad: str = "media"  # alta, media, baja


class RecomendacionUpdate(BaseModel):
    tipo_recomendacion: Optional[str] = None
    descripcion: Optional[str] = None
    prioridad: Optional[str] = None
    estado: Optional[str] = None


# GET todas las recomendaciones
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
                   r.prioridad, r.estado, r.fecha_creacion, r.fecha_actualizacion
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

        if estado:
            query += " AND r.estado = %s"
            params.append(estado)

        query += " ORDER BY r.fecha_creacion DESC"

        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        result = cursor.fetchall()
        cursor.close()
        return result if result else []
    except Exception as e:
        cursor.close()
        return []


# GET una recomendación
@router.get("/{recomendacion_id}")
def obtener_recomendacion(recomendacion_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT r.recomendacion_id, r.estudiante_id, e.nombre as estudiante_nombre,
                   r.materia_id, m.nombre as materia_nombre, r.tipo_recomendacion, r.descripcion,
                   r.prioridad, r.estado, r.fecha_creacion, r.fecha_actualizacion
            FROM sira.recomendacion r
            JOIN sira.estudiante e ON r.estudiante_id = e.estudiante_id
            LEFT JOIN sira.materia m ON r.materia_id = m.materia_id
            WHERE r.recomendacion_id = %s
            """,
            (recomendacion_id,),
        )
        row = cursor.fetchone()
        cursor.close()
        if not row:
            raise HTTPException(status_code=404, detail="Recomendación no encontrada")
        return row
    except HTTPException:
        raise
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error al obtener recomendación: {str(e)}")


# POST crear recomendación
@router.post("", status_code=201)
def crear_recomendacion(data: RecomendacionCreate, db=Depends(get_db)):
    cursor = db.cursor()

    # Validar que el estudiante existe
    cursor.execute(
        "SELECT estudiante_id FROM sira.estudiante WHERE estudiante_id = %s",
        (data.estudiante_id,),
    )
    if not cursor.fetchone():
        cursor.close()
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    # Validar que la materia existe si se proporciona
    if data.materia_id:
        cursor.execute(
            "SELECT materia_id FROM sira.materia WHERE materia_id = %s",
            (data.materia_id,),
        )
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Materia no encontrada")

    # Insertar recomendación
    try:
        cursor.execute(
            """
            INSERT INTO sira.recomendacion 
            (estudiante_id, materia_id, tipo_recomendacion, descripcion, prioridad, estado)
            VALUES (%s, %s, %s, %s, %s, 'activa')
            """,
            (data.estudiante_id, data.materia_id, data.tipo_recomendacion, data.descripcion, data.prioridad),
        )
        db.commit()

        # Obtener la recomendación creada
        cursor.execute(
            """
            SELECT r.recomendacion_id, r.estudiante_id, e.nombre as estudiante_nombre,
                   r.materia_id, m.nombre as materia_nombre, r.tipo_recomendacion, r.descripcion,
                   r.prioridad, r.estado, r.fecha_creacion, r.fecha_actualizacion
            FROM sira.recomendacion r
            JOIN sira.estudiante e ON r.estudiante_id = e.estudiante_id
            LEFT JOIN sira.materia m ON r.materia_id = m.materia_id
            WHERE r.recomendacion_id = LAST_INSERT_ID()
            """
        )
        result = cursor.fetchone()
        cursor.close()
        return result

    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=400, detail=str(e))


# PUT actualizar recomendación
@router.put("/{recomendacion_id}")
def actualizar_recomendacion(
    recomendacion_id: int, data: RecomendacionUpdate, db=Depends(get_db)
):
    cursor = db.cursor(dictionary=True)

    # Verificar que existe
    cursor.execute(
        "SELECT recomendacion_id FROM sira.recomendacion WHERE recomendacion_id = %s",
        (recomendacion_id,),
    )
    if not cursor.fetchone():
        cursor.close()
        raise HTTPException(status_code=404, detail="Recomendación no encontrada")

    # Actualizar
    update_fields = []
    update_values = []

    if data.tipo_recomendacion:
        update_fields.append("tipo_recomendacion = %s")
        update_values.append(data.tipo_recomendacion)

    if data.descripcion:
        update_fields.append("descripcion = %s")
        update_values.append(data.descripcion)

    if data.prioridad:
        update_fields.append("prioridad = %s")
        update_values.append(data.prioridad)

    if data.estado:
        update_fields.append("estado = %s")
        update_values.append(data.estado)

    if not update_fields:
        cursor.close()
        raise HTTPException(status_code=400, detail="No hay campos para actualizar")

    update_values.append(recomendacion_id)
    query = f"UPDATE sira.recomendacion SET {', '.join(update_fields)} WHERE recomendacion_id = %s"

    try:
        cursor.execute(query, update_values)
        db.commit()
        # Obtener la recomendación actualizada
        cursor.execute(
            """
            SELECT r.recomendacion_id, r.estudiante_id, e.nombre as estudiante_nombre,
                   r.materia_id, m.nombre as materia_nombre, r.tipo_recomendacion, r.descripcion,
                   r.prioridad, r.estado, r.fecha_creacion, r.fecha_actualizacion
            FROM sira.recomendacion r
            JOIN sira.estudiante e ON r.estudiante_id = e.estudiante_id
            LEFT JOIN sira.materia m ON r.materia_id = m.materia_id
            WHERE r.recomendacion_id = %s
            """,
            (recomendacion_id,),
        )
        result = cursor.fetchone() or {"mensaje": "Recomendación actualizada"}
        cursor.close()
        return result
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=400, detail=str(e))


# DELETE eliminar recomendación
@router.delete("/{recomendacion_id}")
def eliminar_recomendacion(recomendacion_id: int, db=Depends(get_db)):
    cursor = db.cursor()

    # Verificar que existe
    cursor.execute(
        "SELECT recomendacion_id FROM sira.recomendacion WHERE recomendacion_id = %s",
        (recomendacion_id,),
    )
    if not cursor.fetchone():
        cursor.close()
        raise HTTPException(status_code=404, detail="Recomendación no encontrada")

    try:
        cursor.execute(
            "DELETE FROM sira.recomendacion WHERE recomendacion_id = %s", (recomendacion_id,)
        )
        db.commit()
        cursor.close()
        return {"mensaje": "Recomendación eliminada"}
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=400, detail=str(e))


# POST auto-generar recomendación por calificación
@router.post("/generar/por-calificacion/{calificacion_id}")
def generar_recomendacion_por_calificacion(calificacion_id: int, db=Depends(get_db)):
    """
    Auto-genera una recomendación basada en la calificación del estudiante.
    Si ya existe una recomendación para esa materia, la actualiza.
    """
    cursor = db.cursor(dictionary=True)
    try:
        # Obtener la calificación
        cursor.execute("""
            SELECT c.calificacion_id, c.estudiante_id, c.materia_id, c.nota_final, c.estado
            FROM sira.calificacion c
            WHERE c.calificacion_id = %s
        """, (calificacion_id,))
        cal = cursor.fetchone()
        
        if not cal:
            cursor.close()
            raise HTTPException(status_code=404, detail="Calificación no encontrada")
        
        # No generar si el estado no es aprobado o reprobado
        if cal['estado'] == 'en_curso':
            cursor.close()
            raise HTTPException(status_code=400, detail="La calificación debe estar finalizada")
        
        # Generar recomendación con la utilidad
        rec_data = generar_recomendaciones_por_calificacion(
            cal['nota_final'],
            cal['estudiante_id'],
            cal['materia_id']
        )
        
        # Verificar si ya existe una recomendación para esta materia y estudiante
        cursor.execute("""
            SELECT recomendacion_id FROM sira.recomendacion
            WHERE estudiante_id = %s AND materia_id = %s AND estado = 'activa'
        """, (cal['estudiante_id'], cal['materia_id']))
        
        existing = cursor.fetchone()
        
        if existing:
            # Actualizar la existente
            cursor.execute("""
                UPDATE sira.recomendacion
                SET tipo_recomendacion = %s,
                    descripcion = %s,
                    prioridad = %s
                WHERE recomendacion_id = %s
            """, (rec_data['tipo_recomendacion'], rec_data['descripcion'],
                  rec_data['prioridad'], existing['recomendacion_id']))
            db.commit()
            rec_id = existing['recomendacion_id']
        else:
            # Crear nueva
            cursor.execute("""
                INSERT INTO sira.recomendacion
                (estudiante_id, materia_id, tipo_recomendacion, descripcion, prioridad, estado, fuente)
                VALUES (%s, %s, %s, %s, %s, 'activa', 'automatica')
            """, (rec_data['estudiante_id'], rec_data['materia_id'],
                  rec_data['tipo_recomendacion'], rec_data['descripcion'],
                  rec_data['prioridad']))
            db.commit()
            rec_id = cursor.lastrowid
        
        # Obtener la recomendación creada/actualizada
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


# POST calificar una recomendación
@router.post("/{recomendacion_id}/calificar")
def calificar_recomendacion(recomendacion_id: int, body: dict, db=Depends(get_db)):
    """
    Califica una recomendación (por ej. con estrellas del 1-5)
    """
    cursor = db.cursor(dictionary=True)
    try:
        # Verificar que existe
        cursor.execute(
            "SELECT recomendacion_id FROM sira.recomendacion WHERE recomendacion_id = %s",
            (recomendacion_id,),
        )
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Recomendación no encontrada")
        
        # Actualizar estado de la recomendación a resuelta
        cursor.execute(
            """UPDATE sira.recomendacion SET estado = 'resuelta' 
               WHERE recomendacion_id = %s""",
            (recomendacion_id,),
        )
        db.commit()
        cursor.close()
        return {"mensaje": "Recomendación calificada y marcada como resuelta", "recomendacion_id": recomendacion_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=str(e))


# POST crear recomendación y generar evaluación de 5 preguntas automáticamente
@router.post("/crear-con-evaluacion", status_code=201)
def crear_recomendacion_con_evaluacion(data: RecomendacionCreate, db=Depends(get_db)):
    """
    Crea una recomendación y automáticamente genera una evaluación
    de 5 preguntas de opción múltiple basada en el tipo de recomendación.
    """
    cursor = db.cursor(dictionary=True)
    try:
        # Verificar estudiante
        cursor.execute(
            "SELECT nombre FROM sira.estudiante WHERE estudiante_id = %s",
            (data.estudiante_id,)
        )
        est = cursor.fetchone()
        if not est:
            cursor.close()
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")

        if data.materia_id:
            cursor.execute(
                "SELECT nombre FROM sira.materia WHERE materia_id = %s",
                (data.materia_id,)
            )
            mat = cursor.fetchone()
            materia_nombre = mat['nombre'] if mat else "la materia"
        else:
            materia_nombre = "sus estudios"

        # Insertar recomendación
        cursor.execute(
            """INSERT INTO sira.recomendacion
               (estudiante_id, materia_id, tipo_recomendacion, descripcion, prioridad, estado, fuente)
               VALUES (%s, %s, %s, %s, %s, 'activa', 'manual')""",
            (data.estudiante_id, data.materia_id, data.tipo_recomendacion,
             data.descripcion, data.prioridad)
        )
        db.commit()
        rec_id = cursor.lastrowid

        # Generar 5 preguntas según el tipo de recomendación
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
        preguntas = preguntas_por_tipo.get(tipo_key,
            preguntas_por_tipo.get("mejora_academica"))

        # Crear evaluación
        titulo = f"Evaluación: {data.tipo_recomendacion.replace('_', ' ').title()} — {est['nombre']}"
        cursor.execute(
            "INSERT INTO sira.evaluacion (recomendacion_id, titulo, descripcion) VALUES (%s, %s, %s)",
            (rec_id, titulo, f"Evaluación de seguimiento para la recomendación: {data.descripcion[:100]}")
        )
        db.commit()
        eval_id = cursor.lastrowid

        # Insertar 5 preguntas con opciones
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

        # Retornar recomendación + evaluación creada
        cursor.execute(
            """SELECT r.recomendacion_id, r.estudiante_id, e.nombre as estudiante_nombre,
                      r.materia_id, m.nombre as materia_nombre, r.tipo_recomendacion,
                      r.descripcion, r.prioridad, r.estado, r.fecha_creacion
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