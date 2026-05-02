from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from database import get_db

router = APIRouter()


class PreguntaPersonal(BaseModel):
    pregunta_clave: str
    valor_respuesta: str


# ─────────────────────────────────────────────────────────────────────────────
# ALGORITMO DE RECOMENDACIONES
# Reglas implementadas:
#   1. Promedio general muy bajo (<2.0)       → apoyo urgente
#   2. Promedio bajo (2.0–2.5)                → apoyo académico
#   3. Promedio en riesgo (2.5–3.0)           → refuerzo
#   4. Promedio excelente (>=3.8)             → excelencia / retos
#   5. Materias reprobadas (<2.0)             → recuperación urgente
#   6. Materias en riesgo (2.0–2.5)           → refuerzo por materia
#   7. Materias sobresalientes (>=4.5)        → profundización
#   8. Alta varianza entre materias           → inconsistencia académica
#   9. Muchas materias activas                → carga académica
#  10. Respuesta: dificultad de tiempo alta   → gestión del tiempo
#  11. Respuesta: motivación baja             → apoyo motivacional
#  12. Respuesta: área de interés definida    → orientación vocacional
#  13. Sin calificaciones registradas         → orientación inicial
#  14. Solo una materia aprobada              → continuidad académica
#  15. Todas las materias aprobadas >= 3.0    → felicitación + siguiente nivel
# ─────────────────────────────────────────────────────────────────────────────

def generar_recomendaciones_automaticas(db, estudiante_id: int) -> List[dict]:
    recomendaciones = []
    cursor = db.cursor(dictionary=True)

    try:
        # ── Datos del estudiante ─────────────────────────────────────────────
        cursor.execute(
            "SELECT * FROM sira.estudiante WHERE estudiante_id = %s",
            (estudiante_id,),
        )
        estudiante = cursor.fetchone()
        if not estudiante:
            return []

        promedio_general = float(estudiante.get("promedio_general") or 0)

        # ── Calificaciones ───────────────────────────────────────────────────
        cursor.execute(
            """
            SELECT c.*, m.nombre AS materia_nombre, m.creditos
            FROM sira.calificacion c
            JOIN sira.materia m ON c.materia_id = m.materia_id
            WHERE c.estudiante_id = %s
            ORDER BY c.nota_final ASC
            """,
            (estudiante_id,),
        )
        calificaciones = cursor.fetchall()

        # ── Respuestas personales ────────────────────────────────────────────
        cursor.execute(
            "SELECT pregunta_clave, valor_respuesta FROM sira.respuesta_personal WHERE estudiante_id = %s",
            (estudiante_id,),
        )
        resp_raw = cursor.fetchall()
        resp = {r["pregunta_clave"]: r["valor_respuesta"].strip().lower() for r in resp_raw}

        notas = [float(c.get("nota_final") or 0) for c in calificaciones if c.get("nota_final")]

        # ════════════════════════════════════════════════════════════════════
        # REGLA 13: Sin calificaciones
        # ════════════════════════════════════════════════════════════════════
        if not calificaciones:
            recomendaciones.append({
                "tipo_recomendacion": "orientacion_inicial",
                "descripcion": (
                    "No tienes calificaciones registradas aún. "
                    "Asegúrate de estar inscrito en tus materias, asiste a todas las clases "
                    "y habla con tu coordinador para planificar tu semestre."
                ),
                "prioridad": "media",
                "razon": "Sin calificaciones registradas",
            })
            cursor.close()
            return recomendaciones

        # ════════════════════════════════════════════════════════════════════
        # REGLAS DE PROMEDIO GENERAL
        # ════════════════════════════════════════════════════════════════════

        # REGLA 1: Promedio muy bajo (<2.0) — urgente
        if promedio_general > 0 and promedio_general < 2.0:
            recomendaciones.append({
                "tipo_recomendacion": "apoyo_urgente",
                "descripcion": (
                    f"Tu promedio general es {promedio_general:.2f}, lo cual indica riesgo académico grave. "
                    "Es urgente que te acerques a la coordinación académica, solicites tutorías inmediatas "
                    "y revises tu carga de materias para este semestre."
                ),
                "prioridad": "alta",
                "razon": f"Promedio {promedio_general:.2f} está por debajo de 2.0 — riesgo de pérdida de semestre",
            })

        # REGLA 2: Promedio bajo (2.0–2.5)
        elif 2.0 <= promedio_general < 2.5:
            recomendaciones.append({
                "tipo_recomendacion": "apoyo_academico",
                "descripcion": (
                    f"Tu promedio de {promedio_general:.2f} está en zona de alerta. "
                    "Te recomendamos asistir a tutorías grupales, formar grupos de estudio "
                    "y dedicar al menos 2 horas diarias de estudio adicional."
                ),
                "prioridad": "alta",
                "razon": f"Promedio {promedio_general:.2f} en zona de alerta (2.0–2.5)",
            })

        # REGLA 3: Promedio en riesgo (2.5–3.0)
        elif 2.5 <= promedio_general < 3.0:
            recomendaciones.append({
                "tipo_recomendacion": "refuerzo",
                "descripcion": (
                    f"Con un promedio de {promedio_general:.2f} estás cerca del nivel satisfactorio. "
                    "Identifica tus materias más débiles y refuérzalas con práctica constante. "
                    "Un pequeño esfuerzo extra puede subir tu promedio significativamente."
                ),
                "prioridad": "media",
                "razon": f"Promedio {promedio_general:.2f} justo por debajo de 3.0",
            })

        # REGLA 4: Promedio excelente (>=3.8)
        elif promedio_general >= 3.8:
            recomendaciones.append({
                "tipo_recomendacion": "excelencia",
                "descripcion": (
                    f"¡Excelente! Tu promedio de {promedio_general:.2f} es sobresaliente. "
                    "Considera participar en programas de intercambio académico, semilleros de investigación "
                    "o proyectos de liderazgo estudiantil para potenciar aún más tu perfil."
                ),
                "prioridad": "baja",
                "razon": f"Promedio excepcional {promedio_general:.2f}",
            })

        # ════════════════════════════════════════════════════════════════════
        # REGLAS POR MATERIAS ESPECÍFICAS
        # ════════════════════════════════════════════════════════════════════

        materias_reprobadas = [c for c in calificaciones if (c.get("nota_final") or 0) < 2.0]
        materias_riesgo = [c for c in calificaciones if 2.0 <= (c.get("nota_final") or 0) < 2.5]
        materias_sobresalientes = [c for c in calificaciones if (c.get("nota_final") or 0) >= 4.5]

        # REGLA 5: Materias reprobadas
        for mat in materias_reprobadas[:3]:
            recomendaciones.append({
                "tipo_recomendacion": "recuperacion_urgente",
                "descripcion": (
                    f"Tienes {mat['nota_final']:.1f} en {mat['materia_nombre']}, lo cual es reprobado. "
                    "Habla de inmediato con tu profesor para opciones de recuperación, "
                    "habilitación o nivelación antes de que termine el semestre."
                ),
                "prioridad": "alta",
                "razon": f"Nota {mat['nota_final']} reprobatoria en {mat['materia_nombre']}",
                "materia_id": mat.get("materia_id"),
            })

        # REGLA 6: Materias en riesgo (2.0–2.5)
        for mat in materias_riesgo[:2]:
            recomendaciones.append({
                "tipo_recomendacion": "refuerzo_materia",
                "descripcion": (
                    f"Tu nota en {mat['materia_nombre']} es {mat['nota_final']:.1f}, en zona de riesgo. "
                    "Asiste a asesorías, practica ejercicios adicionales y no faltes a clases."
                ),
                "prioridad": "media",
                "razon": f"Nota {mat['nota_final']} en zona de riesgo en {mat['materia_nombre']}",
                "materia_id": mat.get("materia_id"),
            })

        # REGLA 7: Materias sobresalientes
        if materias_sobresalientes:
            nombres = ", ".join([m["materia_nombre"] for m in materias_sobresalientes[:2]])
            recomendaciones.append({
                "tipo_recomendacion": "profundizacion",
                "descripcion": (
                    f"Tienes notas excepcionales en {nombres}. "
                    "Considera profundizar en estas áreas con cursos avanzados, "
                    "certificaciones externas o proyectos de investigación relacionados."
                ),
                "prioridad": "baja",
                "razon": f"Desempeño sobresaliente (>=4.5) en {nombres}",
            })

        # ════════════════════════════════════════════════════════════════════
        # REGLA 8: Alta varianza entre materias (inconsistencia)
        # ════════════════════════════════════════════════════════════════════
        if len(notas) >= 3:
            nota_max = max(notas)
            nota_min = min(notas)
            varianza = nota_max - nota_min
            if varianza >= 2.0:
                recomendaciones.append({
                    "tipo_recomendacion": "inconsistencia_academica",
                    "descripcion": (
                        f"Existe una diferencia de {varianza:.1f} puntos entre tu mejor y peor nota. "
                        "Esta inconsistencia sugiere que algunos temas o estilos de estudio no son uniformes. "
                        "Trata de aplicar las mismas técnicas que te funcionan en las materias buenas a las que tienes dificultad."
                    ),
                    "prioridad": "media",
                    "razon": f"Diferencia de {varianza:.1f} puntos entre materias (max {nota_max:.1f}, min {nota_min:.1f})",
                })

        # ════════════════════════════════════════════════════════════════════
        # REGLA 9: Carga académica alta (>=6 materias)
        # ════════════════════════════════════════════════════════════════════
        materias_activas = [c for c in calificaciones if c.get("estado") in ("activa", "cursando", None)]
        if len(materias_activas) >= 6:
            recomendaciones.append({
                "tipo_recomendacion": "carga_academica",
                "descripcion": (
                    f"Estás cursando {len(materias_activas)} materias simultáneamente. "
                    "Una carga alta puede afectar tu desempeño. Evalúa si puedes reducirla "
                    "y prioriza las materias más importantes para tu carrera."
                ),
                "prioridad": "media",
                "razon": f"{len(materias_activas)} materias activas simultáneas",
            })

        # REGLA 14: Solo una materia aprobada
        aprobadas = [c for c in calificaciones if (c.get("nota_final") or 0) >= 3.0]
        if len(aprobadas) == 1 and len(calificaciones) > 2:
            recomendaciones.append({
                "tipo_recomendacion": "continuidad_academica",
                "descripcion": (
                    "Solo tienes una materia por encima de 3.0. Es importante que refuerces tu rutina "
                    "de estudio y busques apoyo en las demás materias para no quedar en riesgo de pérdida de semestre."
                ),
                "prioridad": "alta",
                "razon": "Muy pocas materias con nota aprobatoria",
            })

        # REGLA 15: Todas las materias >= 3.0
        if notas and all(n >= 3.0 for n in notas) and promedio_general >= 3.0:
            recomendaciones.append({
                "tipo_recomendacion": "siguiente_nivel",
                "descripcion": (
                    "¡Aprobaste todas tus materias! Para seguir creciendo considera "
                    "inscribirte en electivas de tu interés, participar en talleres extracurriculares "
                    "o hacer voluntariado académico como monitor."
                ),
                "prioridad": "baja",
                "razon": "Todas las materias aprobadas con promedio >= 3.0",
            })

        # ════════════════════════════════════════════════════════════════════
        # REGLAS DE RESPUESTAS PERSONALES
        # ════════════════════════════════════════════════════════════════════

        # REGLA 10: Dificultad de tiempo
        dificultad_tiempo = resp.get("dificultad_tiempo", "")
        if dificultad_tiempo in ("mucha", "alta", "bastante"):
            recomendaciones.append({
                "tipo_recomendacion": "gestion_tiempo",
                "descripcion": (
                    "Reportaste dificultades con la gestión del tiempo. "
                    "Te recomendamos usar la técnica Pomodoro (25 min estudio / 5 min descanso), "
                    "crear un horario semanal fijo y usar apps como Notion o Google Calendar para organizar tus tareas."
                ),
                "prioridad": "alta",
                "razon": "Reportó dificultad alta con gestión de tiempo",
            })
        elif dificultad_tiempo in ("poca", "algo"):
            recomendaciones.append({
                "tipo_recomendacion": "gestion_tiempo",
                "descripcion": (
                    "Tienes algo de dificultad gestionando el tiempo. "
                    "Intenta planificar tu semana cada domingo, definiendo bloques de estudio para cada materia."
                ),
                "prioridad": "baja",
                "razon": "Reportó dificultad leve con gestión de tiempo",
            })

        # REGLA 11: Motivación baja
        motivacion = resp.get("motivacion", "")
        if motivacion in ("baja", "muy_baja", "poca"):
            recomendaciones.append({
                "tipo_recomendacion": "apoyo_motivacional",
                "descripcion": (
                    "Tu motivación académica está baja. Considera hablar con un consejero estudiantil, "
                    "reconectar con las razones por las que elegiste tu carrera, "
                    "y buscar grupos de estudio que te den energía y compañía."
                ),
                "prioridad": "media",
                "razon": f"Motivación reportada como '{motivacion}'",
            })

        # REGLA 12: Área de interés definida
        areas = resp.get("areas_interes", "").strip()
        if areas and areas not in ("ninguna", "no sé", "no se"):
            recomendaciones.append({
                "tipo_recomendacion": "orientacion_vocacional",
                "descripcion": (
                    f"Tienes interés en '{areas}'. Te recomendamos explorar electivas relacionadas, "
                    "buscar grupos estudiantiles de ese tema y conectar con profesores "
                    "que trabajen en esa área para mentorías o proyectos."
                ),
                "prioridad": "baja",
                "razon": f"Interés específico declarado: {areas}",
            })

        cursor.close()
        return recomendaciones

    except Exception as e:
        cursor.close()
        print(f"[ERROR] Algoritmo recomendaciones: {str(e)}")
        return []


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/generar/{estudiante_id}", status_code=201)
def generar_y_guardar_recomendaciones(estudiante_id: int, db=Depends(get_db)):
    """Genera recomendaciones con el algoritmo automático y las guarda en BD"""
    cursor = db.cursor()
    try:
        cursor.execute(
            "SELECT estudiante_id FROM sira.estudiante WHERE estudiante_id = %s",
            (estudiante_id,),
        )
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")

        recomendaciones = generar_recomendaciones_automaticas(db, estudiante_id)
        guardadas = []

        for rec in recomendaciones:
            # Evitar duplicados activos del mismo tipo
            cursor.execute(
                """
                SELECT recomendacion_id FROM sira.recomendacion
                WHERE estudiante_id = %s AND tipo_recomendacion = %s AND estado = 'activa'
                LIMIT 1
                """,
                (estudiante_id, rec["tipo_recomendacion"]),
            )
            if cursor.fetchone():
                continue

            cursor.execute(
                """
                INSERT INTO sira.recomendacion
                (estudiante_id, materia_id, tipo_recomendacion, descripcion, prioridad, estado)
                VALUES (%s, %s, %s, %s, %s, 'activa')
                """,
                (
                    estudiante_id,
                    rec.get("materia_id"),
                    rec["tipo_recomendacion"],
                    rec["descripcion"],
                    rec["prioridad"],
                ),
            )
            guardadas.append({
                "tipo": rec["tipo_recomendacion"],
                "prioridad": rec["prioridad"],
                "razon": rec.get("razon", ""),
            })

        db.commit()
        cursor.close()
        return {
            "status": "éxito",
            "estudiante_id": estudiante_id,
            "recomendaciones_generadas": len(guardadas),
            "detalles": guardadas,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/preguntas-personales/{estudiante_id}")
def guardar_respuestas_personales(
    estudiante_id: int,
    respuestas: List[PreguntaPersonal],
    db=Depends(get_db),
):
    cursor = db.cursor()
    try:
        cursor.execute(
            "SELECT estudiante_id FROM sira.estudiante WHERE estudiante_id = %s",
            (estudiante_id,),
        )
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")

        for resp in respuestas:
            cursor.execute(
                """
                INSERT INTO sira.respuesta_personal (estudiante_id, pregunta_clave, valor_respuesta)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE valor_respuesta = VALUES(valor_respuesta), fecha_respuesta = NOW()
                """,
                (estudiante_id, resp.pregunta_clave, resp.valor_respuesta),
            )

        db.commit()
        cursor.close()
        return {
            "status": "éxito",
            "mensaje": f"Se guardaron {len(respuestas)} respuestas",
            "estudiante_id": estudiante_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/preguntas-personales/{estudiante_id}")
def obtener_respuestas_personales(estudiante_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT pregunta_clave, valor_respuesta, fecha_respuesta
            FROM sira.respuesta_personal WHERE estudiante_id = %s
            ORDER BY fecha_respuesta DESC
            """,
            (estudiante_id,),
        )
        result = cursor.fetchall()
        cursor.close()
        return result or []
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/sugerencias/{estudiante_id}")
def obtener_recomendaciones_sugeridas(estudiante_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT * FROM sira.recomendacion
            WHERE estudiante_id = %s AND estado = 'activa'
            ORDER BY
                CASE prioridad WHEN 'alta' THEN 1 WHEN 'media' THEN 2 WHEN 'baja' THEN 3 END,
                fecha_creacion DESC
            """,
            (estudiante_id,),
        )
        result = cursor.fetchall()
        cursor.close()
        return result or []
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")