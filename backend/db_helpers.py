"""
Utilidades para interacción con la base de datos.

Centraliza funciones comunes como:
- Obtención de columnas dinámicamente
- Construcción de queries SELECT
- Mapeo de tipos de datos
"""

from typing import Optional, Set, Dict, List, Any


def get_table_columns(cursor, table_name: str) -> Set[str]:
    """
    Obtiene el conjunto de columnas de una tabla.
    
    Intenta usar SHOW COLUMNS primero, y cae a INFORMATION_SCHEMA si falla.
    
    Args:
        cursor: Cursor de conexión MySQL
        table_name: Nombre de la tabla
        
    Returns:
        Set con los nombres de columnas en minúsculas
    """
    try:
        cursor.execute(f"SHOW COLUMNS FROM `{table_name}`")
        return {row[0].lower() if isinstance(row, tuple) else row['Field'].lower() 
                for row in cursor.fetchall()}
    except Exception:
        try:
            cursor.execute("""
                SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s
            """, (table_name,))
            return {row['COLUMN_NAME'].lower() for row in cursor.fetchall()}
        except Exception:
            return set()


def build_select_clause(
    cursor, 
    table_name: str, 
    required_cols: List[str], 
    optional_cols: Optional[List[str]] = None,
    prefix: str = ""
) -> str:
    """
    Construye una cláusula SELECT adaptada a las columnas existentes en la tabla.
    
    Args:
        cursor: Cursor de conexión MySQL
        table_name: Nombre de la tabla
        required_cols: Columnas que DEBEN estar presentes
        optional_cols: Columnas que se incluyen si existen
        prefix: Prefijo para las columnas (ej: "e." para alias)
        
    Returns:
        String con la cláusula SELECT
        
    Raises:
        ValueError: Si alguna columna requerida no existe
    """
    existing_cols = get_table_columns(cursor, table_name)
    
    # Validar columnas requeridas
    missing = [col for col in required_cols if col.lower() not in existing_cols]
    if missing:
        raise ValueError(f"Columnas faltantes en tabla '{table_name}': {', '.join(missing)}")
    
    # Construir SELECT con requeridas
    select_parts = [f"{prefix}{col}" for col in required_cols]
    
    # Agregar opcionales si existen
    if optional_cols:
        for col in optional_cols:
            if col.lower() in existing_cols:
                select_parts.append(f"{prefix}{col}")
    
    return ", ".join(select_parts)


def validate_column_exists(cursor, table_name: str, column_name: str) -> bool:
    """
    Verifica si una columna existe en una tabla.
    
    Args:
        cursor: Cursor de conexión MySQL
        table_name: Nombre de la tabla
        column_name: Nombre de la columna
        
    Returns:
        True si la columna existe, False en caso contrario
    """
    cols = get_table_columns(cursor, table_name)
    return column_name.lower() in cols


def safe_getitem(row: Any, key: str, default: Any = None) -> Any:
    """
    Accede seguro a un elemento de un row de cursor (dict o tuple).
    
    Args:
        row: Row del cursor (puede ser dict o tuple)
        key: Clave/índice a acceder
        default: Valor por defecto si no existe
        
    Returns:
        Valor o default
    """
    try:
        if isinstance(row, dict):
            return row.get(key, default)
        else:
            # Si es tuple, asumimos que el cursor tiene columnas nombradas
            return getattr(row, key, default) if hasattr(row, key) else default
    except (KeyError, AttributeError, IndexError):
        return default


def count_non_null_values(values: List[Optional[float]]) -> int:
    """
    Cuenta cuántos valores no None hay en una lista.
    
    Args:
        values: Lista de valores (pueden ser None)
        
    Returns:
        Cantidad de valores no None
    """
    return sum(1 for v in values if v is not None)


def get_non_null_values(values: List[Optional[float]]) -> List[float]:
    """
    Filtra una lista para devolver solo valores no None.
    
    Args:
        values: Lista de valores (pueden ser None)
        
    Returns:
        Lista filtrada sin None
    """
    return [v for v in values if v is not None]
