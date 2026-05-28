"""
Excepciones personalizadas del proyecto.

Define excepciones específicas del dominio para:
- Validación de datos
- Errores de negocio
- Errores de acceso
"""

from fastapi import HTTPException, status
from typing import Optional, Any, Dict


class SIRAException(HTTPException):
    """Excepción base del proyecto SIRA."""
    
    def __init__(
        self,
        detail: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        headers: Optional[Dict[str, str]] = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class ValidationException(SIRAException):
    """Error en validación de datos de entrada."""
    
    def __init__(self, detail: str, headers: Optional[Dict[str, str]] = None):
        super().__init__(
            detail=f"Error de validación: {detail}",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            headers=headers,
        )


class ResourceNotFoundException(SIRAException):
    """Recurso no encontrado."""
    
    def __init__(
        self,
        resource_type: str,
        resource_id: Any = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        detail = f"{resource_type} no encontrado"
        if resource_id:
            detail += f" (ID: {resource_id})"
        super().__init__(
            detail=detail,
            status_code=status.HTTP_404_NOT_FOUND,
            headers=headers,
        )


class DuplicateResourceException(SIRAException):
    """El recurso ya existe (violación de uniqueness)."""
    
    def __init__(
        self,
        resource_type: str,
        field: str = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        detail = f"{resource_type} duplicado"
        if field:
            detail += f" (Campo: {field})"
        super().__init__(
            detail=detail,
            status_code=status.HTTP_409_CONFLICT,
            headers=headers,
        )


class UnauthorizedException(SIRAException):
    """Autenticación fallida."""
    
    def __init__(self, detail: str = "Credenciales inválidas", headers: Optional[Dict[str, str]] = None):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers=headers,
        )


class ForbiddenException(SIRAException):
    """Usuario no tiene permiso para acceder al recurso."""
    
    def __init__(self, detail: str = "Acceso denegado", headers: Optional[Dict[str, str]] = None):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_403_FORBIDDEN,
            headers=headers,
        )


class InsufficientDataException(SIRAException):
    """No hay suficientes datos para realizar la operación."""
    
    def __init__(
        self,
        operation: str,
        required_fields: list = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        detail = f"Datos insuficientes para {operation}"
        if required_fields:
            detail += f": se requiere al menos {', '.join(required_fields)}"
        super().__init__(
            detail=detail,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            headers=headers,
        )


class ConstraintViolationException(SIRAException):
    """Violación de restricción de base de datos."""
    
    def __init__(
        self,
        constraint_name: str,
        detail: str = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        msg = f"Violación de restricción: {constraint_name}"
        if detail:
            msg += f". {detail}"
        super().__init__(
            detail=msg,
            status_code=status.HTTP_409_CONFLICT,
            headers=headers,
        )


class DatabaseException(SIRAException):
    """Error en operación de base de datos."""
    
    def __init__(self, operation: str, details: str = None, headers: Optional[Dict[str, str]] = None):
        msg = f"Error en operación de BD: {operation}"
        if details:
            msg += f". {details}"
        super().__init__(
            detail=msg,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            headers=headers,
        )


class InvalidOperationException(SIRAException):
    """Operación inválida o no permitida en el estado actual."""
    
    def __init__(self, detail: str, headers: Optional[Dict[str, str]] = None):
        super().__init__(
            detail=f"Operación inválida: {detail}",
            status_code=status.HTTP_400_BAD_REQUEST,
            headers=headers,
        )


# ─── Utilidades para manejo de excepciones ───────────────────────────────────


def handle_db_error(e: Exception, operation: str) -> DatabaseException:
    """
    Convierte excepciones de BD a DatabaseException apropiada.
    
    Args:
        e: Excepción original
        operation: Operación que se intentaba realizar
        
    Returns:
        DatabaseException apropiada
    """
    error_msg = str(e).lower()
    
    # Detección de tipos de error comunes
    if "duplicate" in error_msg or "unique" in error_msg:
        return DuplicateResourceException(
            resource_type="Recurso",
            headers={"X-Original-Error": str(e)},
        )
    
    if "not found" in error_msg:
        return ResourceNotFoundException(
            resource_type="Recurso",
            headers={"X-Original-Error": str(e)},
        )
    
    if "constraint" in error_msg:
        return ConstraintViolationException(
            constraint_name="Restricción desconocida",
            detail=str(e),
            headers={"X-Original-Error": str(e)},
        )
    
    return DatabaseException(
        operation=operation,
        details=str(e),
        headers={"X-Original-Error": str(e)},
    )
