"""
Utilidades de autenticación y seguridad.

Proporciona funciones para:
- Hash de contraseñas usando bcrypt
- Verificación de contraseñas
- Validación de emails y datos sensibles
"""

import bcrypt
import re
from typing import Optional

def hash_password(password: str) -> str:
    """
    Hashea una contraseña usando bcrypt con salt rounds=12.
    
    Args:
        password: Contraseña en plaintext
        
    Returns:
        Hash bcrypt codificado como string
        
    Raises:
        ValueError: Si la contraseña está vacía
    """
    if not password or len(password.strip()) == 0:
        raise ValueError("La contraseña no puede estar vacía")
    
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verifica una contraseña contra su hash bcrypt.
    
    Args:
        password: Contraseña en plaintext a verificar
        hashed_password: Hash bcrypt almacenado
        
    Returns:
        True si la contraseña coincide, False en caso contrario
    """
    try:
        return bcrypt.checkpw(
            password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except (ValueError, TypeError):
        return False


def validate_email(email: str) -> bool:
    """
    Valida que el email tenga formato correcto.
    
    Args:
        email: Email a validar
        
    Returns:
        True si el email es válido
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip())) if email else False


def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
    """
    Valida la fortaleza de una contraseña.
    
    Requisitos:
    - Mínimo 8 caracteres
    - Al menos una mayúscula
    - Al menos una minúscula
    - Al menos un dígito
    
    Args:
        password: Contraseña a validar
        
    Returns:
        Tupla (es_válida, mensaje_de_error)
    """
    if not password:
        return False, "La contraseña no puede estar vacía"
    
    if len(password) < 8:
        return False, "La contraseña debe tener mínimo 8 caracteres"
    
    if not any(c.isupper() for c in password):
        return False, "La contraseña debe contener al menos una mayúscula"
    
    if not any(c.islower() for c in password):
        return False, "La contraseña debe contener al menos una minúscula"
    
    if not any(c.isdigit() for c in password):
        return False, "La contraseña debe contener al menos un dígito"
    
    return True, None
