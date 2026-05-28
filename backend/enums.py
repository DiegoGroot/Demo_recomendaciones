"""
Enumeraciones centralizadas del proyecto.

Define constantes y enumeraciones para:
- Tipos de recomendaciones
- Estados académicos
- Estados de calificación
- Roles de usuario
"""

from enum import Enum


class TipoRecomendacion(str, Enum):
    """Tipos de recomendaciones académicas generadas automáticamente."""
    
    RECUPERACION = "recuperacion"
    """Recomendación urgente para estudiantes con bajo desempeño (< 5.0)"""
    
    TUTORIA = "tutoria"
    """Tutoría adicional recomendada para estudiantes con desempeño mediocre (5.0 - 7.0)"""
    
    MEJORA_ACADEMICA = "mejora_academica"
    """Oportunidad de mejora académica para estudiantes con buen desempeño (7.0 - 8.5)"""
    
    ORIENTACION = "orientacion"
    """Orientación académica para estudiantes con excelente desempeño (>= 8.5)"""


class PrioridadRecomendacion(str, Enum):
    """Niveles de prioridad de una recomendación."""
    
    ALTA = "alta"
    """Requiere atención inmediata"""
    
    MEDIA = "media"
    """Requiere atención en plazo corto"""
    
    BAJA = "baja"
    """Información de seguimiento"""


class EstadoAcademico(str, Enum):
    """Estados académicos del estudiante basados en promedio general."""
    
    RIESGO = "riesgo"
    """Promedio < 5.0 - Requiere intervención"""
    
    REGULAR = "regular"
    """Promedio 5.0 - 7.0 - Desempeño dentro de lo esperado"""
    
    BUENO = "bueno"
    """Promedio 7.0 - 8.5 - Desempeño superior"""
    
    EXCELENTE = "excelente"
    """Promedio >= 8.5 - Desempeño excepcional"""


class EstadoCalificacion(str, Enum):
    """Estados de una calificación individual."""
    
    EN_CURSO = "en_curso"
    """La materia está en progreso"""
    
    APROBADO = "aprobado"
    """Nota final >= 6.0"""
    
    REPROBADO = "reprobado"
    """Nota final < 6.0"""


class RolUsuario(str, Enum):
    """Roles de usuario en el sistema."""
    
    SUPER_ADMIN = "super_admin"
    """Acceso total al sistema"""
    
    ADMIN = "administrador"
    """Acceso administrativo general"""
    
    COORDINADOR = "coordinador"
    """Acceso a coordinación académica"""
    
    ESTUDIANTE = "estudiante"
    """Acceso limitado como estudiante"""


class FuenteRecomendacion(str, Enum):
    """Origen de una recomendación."""
    
    AUTOMATICA = "automatica"
    """Generada automáticamente por el sistema"""
    
    MANUAL = "manual"
    """Ingresada manualmente por un docente/coordinador"""


# ─── Diccionarios de Configuración ───────────────────────────────────────────

# Mapeo de rangos de nota a tipo de recomendación
RANGO_RECOMENDACION_MAP = {
    (0, 5.0): TipoRecomendacion.RECUPERACION,
    (5.0, 7.0): TipoRecomendacion.TUTORIA,
    (7.0, 8.5): TipoRecomendacion.MEJORA_ACADEMICA,
    (8.5, 10.0): TipoRecomendacion.ORIENTACION,
}

# Mapeo de rangos de nota a prioridad
RANGO_PRIORIDAD_MAP = {
    (0, 5.0): PrioridadRecomendacion.ALTA,
    (5.0, 7.0): PrioridadRecomendacion.ALTA,
    (7.0, 8.5): PrioridadRecomendacion.MEDIA,
    (8.5, 10.0): PrioridadRecomendacion.BAJA,
}

# Mapeo de rangos de promedio a estado académico
RANGO_ESTADO_ACADEMICO_MAP = {
    (0, 5.0): EstadoAcademico.RIESGO,
    (5.0, 7.0): EstadoAcademico.REGULAR,
    (7.0, 8.5): EstadoAcademico.BUENO,
    (8.5, 10.0): EstadoAcademico.EXCELENTE,
}


def get_tipo_recomendacion(nota: float) -> TipoRecomendacion:
    """
    Determina el tipo de recomendación basado en la nota.
    
    Args:
        nota: Nota final (0-10)
        
    Returns:
        TipoRecomendacion correspondiente
    """
    for (min_nota, max_nota), tipo in RANGO_RECOMENDACION_MAP.items():
        if min_nota <= nota < max_nota:
            return tipo
    return TipoRecomendacion.ORIENTACION


def get_prioridad_recomendacion(nota: float) -> PrioridadRecomendacion:
    """
    Determina la prioridad basada en la nota.
    
    Args:
        nota: Nota final (0-10)
        
    Returns:
        PrioridadRecomendacion correspondiente
    """
    for (min_nota, max_nota), prioridad in RANGO_PRIORIDAD_MAP.items():
        if min_nota <= nota < max_nota:
            return prioridad
    return PrioridadRecomendacion.BAJA


def get_estado_academico(promedio: float) -> EstadoAcademico:
    """
    Determina el estado académico basado en el promedio.
    
    Args:
        promedio: Promedio general (0-10)
        
    Returns:
        EstadoAcademico correspondiente
    """
    for (min_prom, max_prom), estado in RANGO_ESTADO_ACADEMICO_MAP.items():
        if min_prom <= promedio < max_prom:
            return estado
    return EstadoAcademico.EXCELENTE
