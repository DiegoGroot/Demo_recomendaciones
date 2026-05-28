"""
Patrón Repository para abstracción de persistencia.

Define interfaces abstractas para:
- CRUD operations
- Consultas comunes
- Transacciones
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, Generic, TypeVar
from exceptions import (
    ResourceNotFoundException,
    DuplicateResourceException,
    DatabaseException,
)

T = TypeVar('T')


class IRepository(ABC, Generic[T]):
    """
    Interfaz base para repositorios.
    
    Define un contrato para operaciones comunes de persistencia.
    Permite inyectar diferentes implementaciones sin afectar el código cliente.
    """
    
    @abstractmethod
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """
        Obtiene todos los registros con paginación.
        
        Args:
            limit: Número máximo de registros
            offset: Desplazamiento para paginación
            
        Returns:
            Lista de entidades
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, id: Any) -> T:
        """
        Obtiene un registro por ID.
        
        Args:
            id: Identificador del registro
            
        Returns:
            Entidad encontrada
            
        Raises:
            ResourceNotFoundException: Si no existe
        """
        pass
    
    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> T:
        """
        Crea un nuevo registro.
        
        Args:
            data: Diccionario con datos de la entidad
            
        Returns:
            Entidad creada con ID
            
        Raises:
            DuplicateResourceException: Si viola uniqueness
            ValidationException: Si falla validación
        """
        pass
    
    @abstractmethod
    async def update(self, id: Any, data: Dict[str, Any]) -> T:
        """
        Actualiza un registro existente.
        
        Args:
            id: Identificador del registro
            data: Diccionario con campos a actualizar
            
        Returns:
            Entidad actualizada
            
        Raises:
            ResourceNotFoundException: Si no existe
            DuplicateResourceException: Si viola uniqueness
        """
        pass
    
    @abstractmethod
    async def delete(self, id: Any) -> bool:
        """
        Elimina un registro.
        
        Args:
            id: Identificador del registro
            
        Returns:
            True si se eliminó, False si no existía
            
        Raises:
            DatabaseException: Si falla la operación
        """
        pass
    
    @abstractmethod
    async def exists(self, id: Any) -> bool:
        """
        Verifica si existe un registro.
        
        Args:
            id: Identificador del registro
            
        Returns:
            True si existe
        """
        pass


class BaseRepository(IRepository[T]):
    """
    Implementación base del repositorio.
    
    Proporciona implementación por defecto para métodos comunes.
    Las subclases pueden sobrescribir según necesidades específicas.
    """
    
    def __init__(self, cursor, table_name: str, id_column: str = "id"):
        """
        Inicializa el repositorio.
        
        Args:
            cursor: Cursor de BD activo
            table_name: Nombre de la tabla en BD
            id_column: Nombre de la columna ID (default: 'id')
        """
        self.cursor = cursor
        self.table_name = table_name
        self.id_column = id_column
    
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Obtiene todos los registros con paginación (implementación por defecto).
        """
        try:
            query = f"SELECT * FROM `{self.table_name}` LIMIT %s OFFSET %s"
            self.cursor.execute(query, (limit, offset))
            return self.cursor.fetchall()
        except Exception as e:
            raise DatabaseException("SELECT ALL", str(e))
    
    async def get_by_id(self, id: Any) -> Dict[str, Any]:
        """
        Obtiene un registro por ID (implementación por defecto).
        """
        try:
            query = f"SELECT * FROM `{self.table_name}` WHERE `{self.id_column}` = %s LIMIT 1"
            self.cursor.execute(query, (id,))
            result = self.cursor.fetchone()
            
            if not result:
                raise ResourceNotFoundException(self.table_name, id)
            
            return result
        except ResourceNotFoundException:
            raise
        except Exception as e:
            raise DatabaseException(f"SELECT BY ID ({id})", str(e))
    
    async def exists(self, id: Any) -> bool:
        """
        Verifica si existe un registro (implementación por defecto).
        """
        try:
            query = f"SELECT 1 FROM `{self.table_name}` WHERE `{self.id_column}` = %s LIMIT 1"
            self.cursor.execute(query, (id,))
            return self.cursor.fetchone() is not None
        except Exception as e:
            raise DatabaseException(f"EXISTS ({id})", str(e))
    
    async def delete(self, id: Any) -> bool:
        """
        Elimina un registro (implementación por defecto).
        """
        try:
            query = f"DELETE FROM `{self.table_name}` WHERE `{self.id_column}` = %s"
            self.cursor.execute(query, (id,))
            return self.cursor.rowcount > 0
        except Exception as e:
            raise DatabaseException(f"DELETE ({id})", str(e))
    
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea un nuevo registro (debe ser implementado por subclases).
        """
        raise NotImplementedError("Subclass must implement create()")
    
    async def update(self, id: Any, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza un registro (debe ser implementado por subclases).
        """
        raise NotImplementedError("Subclass must implement update()")


# ─── Marcador de síncrono vs asíncrono ───────────────────────────────────────


class SyncRepository(IRepository[T]):
    """
    Versión síncrona del repositorio para FastAPI sin async.
    
    Nota: FastAPI es asíncrono, pero MySQL connector es síncrono.
    Esta clase permite usar la API IRepository de forma compatible.
    """
    
    def __init__(self, cursor, table_name: str, id_column: str = "id"):
        self.cursor = cursor
        self.table_name = table_name
        self.id_column = id_column
    
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Obtiene todos los registros con paginación."""
        try:
            query = f"SELECT * FROM `{self.table_name}` LIMIT %s OFFSET %s"
            self.cursor.execute(query, (limit, offset))
            return self.cursor.fetchall()
        except Exception as e:
            raise DatabaseException("SELECT ALL", str(e))
    
    async def get_by_id(self, id: Any) -> Dict[str, Any]:
        """Obtiene un registro por ID."""
        try:
            query = f"SELECT * FROM `{self.table_name}` WHERE `{self.id_column}` = %s LIMIT 1"
            self.cursor.execute(query, (id,))
            result = self.cursor.fetchone()
            
            if not result:
                raise ResourceNotFoundException(self.table_name, id)
            
            return result
        except ResourceNotFoundException:
            raise
        except Exception as e:
            raise DatabaseException(f"SELECT BY ID ({id})", str(e))
    
    async def exists(self, id: Any) -> bool:
        """Verifica si existe un registro."""
        try:
            query = f"SELECT 1 FROM `{self.table_name}` WHERE `{self.id_column}` = %s LIMIT 1"
            self.cursor.execute(query, (id,))
            return self.cursor.fetchone() is not None
        except Exception as e:
            raise DatabaseException(f"EXISTS ({id})", str(e))
    
    async def delete(self, id: Any) -> bool:
        """Elimina un registro."""
        try:
            query = f"DELETE FROM `{self.table_name}` WHERE `{self.id_column}` = %s"
            self.cursor.execute(query, (id,))
            return self.cursor.rowcount > 0
        except Exception as e:
            raise DatabaseException(f"DELETE ({id})", str(e))
    
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Debe ser implementado por subclases."""
        raise NotImplementedError("Subclass must implement create()")
    
    async def update(self, id: Any, data: Dict[str, Any]) -> Dict[str, Any]:
        """Debe ser implementado por subclases."""
        raise NotImplementedError("Subclass must implement update()")
