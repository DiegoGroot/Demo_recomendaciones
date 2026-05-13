def generar_recomendaciones_por_calificacion(nota_final: float, estudiante_id: int, materia_id: int) -> dict:

    # Determinar tipo y prioridad basado en la calificación
    if nota_final < 5.0:
        tipo = "recuperacion"
        prioridad = "alta"
        descripcion = (
            f"Recomendación de recuperación urgente. Tu calificación en la materia fue {nota_final}/5. "
            "Te recomendamos asistir a sesiones de tutoría intensivas y revisar los temas fundamentales."
        )
    elif nota_final < 7.0:
        tipo = "tutoria"
        prioridad = "alta"
        descripcion = (
            f"Necesitas tutoría adicional. Tu calificación fue {nota_final}/5. "
            "Recomendamos sesiones regulares de tutoría para reforzar los conceptos clave."
        )
    elif nota_final < 8.5:
        tipo = "mejora_academica"
        prioridad = "media"
        descripcion = (
            f"Oportunidad de mejora académica. Tu calificación fue {nota_final}/5. "
            "Con dedicación extra, puedes alcanzar un mejor desempeño."
        )
    else:
        tipo = "orientacion"
        prioridad = "baja"
        descripcion = (
            f"Orientación académica. Tu calificación fue {nota_final}/5. "
            "Mantén este buen desempeño y considera profundizar en temas de interés."
        )

    return {
        "estudiante_id": estudiante_id,
        "materia_id": materia_id,
        "tipo_recomendacion": tipo,
        "descripcion": descripcion,
        "prioridad": prioridad,
        "fuente": "automatica",
    }


def determinar_estado_academico(promedio: float) -> str:
    """
    Determina el estado académico basado en el promedio.

    Args:
        promedio: Promedio general del estudiante (0-5)

    Returns:
        str con el estado académico
    """
    if promedio < 5.0:
        return "riesgo"
    elif promedio < 7.0:
        return "regular"
    elif promedio < 8.5:
        return "bueno"
    else:
        return "excelente"