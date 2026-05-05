"""
Utilidades para generar recomendaciones automáticas basadas en el rendimiento académico
"""

def generar_recomendaciones_por_calificacion(nota_final: float, estudiante_id: int, materia_id: int) -> dict:
    """
    Genera una recomendación automática basada en la calificación del estudiante.
    
    Args:
        nota_final: Nota final del estudiante (0-5)
        estudiante_id: ID del estudiante
        materia_id: ID de la materia
    
    Returns:
        dict con los datos de la recomendación a crear
    """
    
    # Determinar tipo y prioridad basado en la calificación
    if nota_final < 2.0:
        tipo = "recuperacion"
        prioridad = "alta"
        descripcion = f"Recomendación de recuperación urgente. Tu calificación en la materia fue {nota_final}/5. Te recomendamos asistir a sesiones de tutoría intensivas y revisar los temas fundamentales."
    elif nota_final < 3.0:
        tipo = "tutoria"
        prioridad = "alta"
        descripcion = f"Necesitas tutoría adicional. Tu calificación fue {nota_final}/5. Recomendamos sesiones regulares de tutoría para reforzar los conceptos clave."
    elif nota_final < 3.5:
        tipo = "mejora_academica"
        prioridad = "media"
        descripcion = f"Oportunidad de mejora académica. Tu calificación fue {nota_final}/5. Con dedicación extra, puedes alcanzar un mejor desempeño."
    else:
        tipo = "orientacion"
        prioridad = "baja"
        descripcion = f"Orientación académica. Tu calificación fue {nota_final}/5. Mantén este buen desempeño y considera profundizar en temas de interés."
    
    return {
        "estudiante_id": estudiante_id,
        "materia_id": materia_id,
        "tipo_recomendacion": tipo,
        "descripcion": descripcion,
        "prioridad": prioridad,
        "fuente": "automatica"
    }


def determinar_estado_academico(promedio: float) -> str:
    """
    Determina el estado académico basado en el promedio.
    
    Args:
        promedio: Promedio general del estudiante (0-5)
    
    Returns:
        str con el estado académico
    """
    if promedio < 2.0:
        return "riesgo"
    elif promedio < 3.0:
        return "regular"
    elif promedio < 3.5:
        return "bueno"
    else:
        return "excelente"
