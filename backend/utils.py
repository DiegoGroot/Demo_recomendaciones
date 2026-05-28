"""
Utilidades de lógica de negocio para recomendaciones académicas.

Módulo dedicado a generar recomendaciones basadas en desempeño.
Responsabilidad única: Generar recomendaciones (ver enums.py para estados académicos).
"""

from typing import Dict, Any
from enums import (
    TipoRecomendacion,
    PrioridadRecomendacion,
    FuenteRecomendacion,
    get_tipo_recomendacion,
    get_prioridad_recomendacion,
)


def generar_recomendacion_automatica(
    nota_final: float,
    estudiante_id: int,
    materia_id: int,
) -> Dict[str, Any]:
    """
    Genera una recomendación académica automática basada en la calificación.
    
    Estrategia:
    - Nota < 5.0: Recuperación urgente
    - Nota 5.0-7.0: Tutoría adicional
    - Nota 7.0-8.5: Oportunidad de mejora
    - Nota >= 8.5: Orientación y profundización
    
    Args:
        nota_final: Nota final de la materia (0-10)
        estudiante_id: ID del estudiante
        materia_id: ID de la materia
        
    Returns:
        Diccionario con datos de recomendación
        
    Raises:
        ValueError: Si nota_final no está en rango 0-10
    """
    if not (0 <= nota_final <= 10):
        raise ValueError(f"Nota debe estar entre 0 y 10, se recibió: {nota_final}")
    
    tipo = get_tipo_recomendacion(nota_final)
    prioridad = get_prioridad_recomendacion(nota_final)
    descripcion = _generar_descripcion(tipo, nota_final)
    
    return {
        "estudiante_id": estudiante_id,
        "materia_id": materia_id,
        "tipo_recomendacion": tipo.value,
        "descripcion": descripcion,
        "prioridad": prioridad.value,
        "fuente": FuenteRecomendacion.AUTOMATICA.value,
    }


def _generar_descripcion(tipo: TipoRecomendacion, nota_final: float) -> str:
    """
    Genera la descripción textual de la recomendación.
    
    Args:
        tipo: Tipo de recomendación
        nota_final: Nota final obtenida
        
    Returns:
        Texto descriptivo de la recomendación
    """
    mapping = {
        TipoRecomendacion.RECUPERACION: (
            f"⚠️  Recomendación de recuperación urgente. Tu calificación en la materia fue {nota_final}/10. "
            "Te recomendamos asistir a sesiones de tutoría intensivas y revisar los temas fundamentales. "
            "Contacta con el coordinador académico para un plan de mejora personalizado."
        ),
        TipoRecomendacion.TUTORIA: (
            f"📚 Necesitas tutoría adicional. Tu calificación fue {nota_final}/10. "
            "Recomendamos sesiones regulares de tutoría para reforzar los conceptos clave. "
            "Esta acción puede mejorar significativamente tu desempeño futuro."
        ),
        TipoRecomendacion.MEJORA_ACADEMICA: (
            f"📈 Oportunidad de mejora académica. Tu calificación fue {nota_final}/10. "
            "Con dedicación extra y revisión de temas complejos, puedes alcanzar un mejor desempeño. "
            "Considera formar grupos de estudio con compañeros."
        ),
        TipoRecomendacion.ORIENTACION: (
            f"🎓 Orientación académica. Tu calificación fue {nota_final}/10. "
            "Excelente desempeño. Mantén este nivel y considera profundizar en temas de interés "
            "en cursos o especializaciones futuras."
        ),
    }
    
    return mapping.get(tipo, f"Recomendación por calificación: {nota_final}/10")


def validar_nota_para_recomendacion(nota_final: float) -> tuple[bool, str]:
    """
    Valida si una nota es válida para generar recomendación.
    
    Args:
        nota_final: Nota a validar (0-10)
        
    Returns:
        Tupla (es_válida, mensaje_error)
    """
    if nota_final is None:
        return False, "La nota final no puede ser None"
    
    try:
        nota = float(nota_final)
    except (TypeError, ValueError):
        return False, f"Nota debe ser un número, se recibió: {type(nota_final).__name__}"
    
    if not (0 <= nota <= 10):
        return False, f"Nota debe estar entre 0 y 10, se recibió: {nota}"
    
    return True, ""
