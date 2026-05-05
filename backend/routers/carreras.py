from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import get_db
from mysql.connector import errors as mysql_errors

router = APIRouter()

class CarreraCreate(BaseModel):
    nombre: str
    codigo: Optional[str] = None      # opcional, se genera automático si no se pasa
    descripcion: Optional[str] = None
    duracion_anios: Optional[int] = None

class CarreraUpdate(BaseModel):
    nombre: Optional[str] = None
    codigo: Optional[str] = None
    descripcion: Optional[str] = None
    duracion_anios: Optional[int] = None
    estado: Optional[str] = None

# GET todas
@router.get("")
def listar_carreras(db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT carrera_id, codigo, nombre, descripcion, duracion_anios, estado, creado_en
            FROM sira.carrera
            ORDER BY nombre
        """)
        result = cursor.fetchall()
        cursor.close()
        return result
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error al listar carreras: {str(e)}")

# GET una
@router.get("/{carrera_id}")
def obtener_carrera(carrera_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT carrera_id, codigo, nombre, descripcion, duracion_anios, estado, creado_en
            FROM sira.carrera WHERE carrera_id = %s
        """, (carrera_id,))
        row = cursor.fetchone()
        cursor.close()
        if not row:
            raise HTTPException(status_code=404, detail="Carrera no encontrada")
        return row
    except HTTPException:
        raise
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=str(e))

# POST crear
@router.post("", status_code=201)
def crear_carrera(data: CarreraCreate, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        # Generar código automático si no se proporciona
        codigo = data.codigo
        if not codigo:
            # Tomar las primeras 3 letras del nombre + número aleatorio
            import re, random
            base = re.sub(r'[^A-Za-z]', '', data.nombre).upper()[:4]
            codigo = f"{base}{random.randint(100,999)}"

        # Verificar duplicado de nombre
        cursor.execute("SELECT carrera_id FROM sira.carrera WHERE nombre = %s", (data.nombre,))
        if cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=409, detail="Ya existe una carrera con ese nombre")

        cursor.execute("""
            INSERT INTO sira.carrera (nombre, codigo, descripcion, duracion_anios, estado)
            VALUES (%s, %s, %s, %s, 'activa')
        """, (data.nombre, codigo, data.descripcion, data.duracion_anios))
        db.commit()
        new_id = cursor.lastrowid
        cursor.execute("SELECT carrera_id, codigo, nombre, descripcion, duracion_anios, estado FROM sira.carrera WHERE carrera_id = %s", (new_id,))
        carrera = cursor.fetchone()
        cursor.close()
        return carrera
    except HTTPException:
        raise
    except mysql_errors.IntegrityError as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=409, detail="Nombre o código de carrera ya registrado")
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error al crear carrera: {str(e)}")

# PUT actualizar
@router.put("/{carrera_id}")
def actualizar_carrera(carrera_id: int, data: CarreraUpdate, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT carrera_id FROM sira.carrera WHERE carrera_id = %s", (carrera_id,))
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Carrera no encontrada")
        campos = {k: v for k, v in data.dict().items() if v is not None}
        if not campos:
            cursor.close()
            raise HTTPException(status_code=400, detail="Sin datos para actualizar")
        set_clause = ", ".join([f"{k} = %s" for k in campos])
        cursor.execute(
            f"UPDATE sira.carrera SET {set_clause} WHERE carrera_id = %s",
            (*campos.values(), carrera_id)
        )
        db.commit()
        cursor.execute("SELECT carrera_id, codigo, nombre, descripcion, duracion_anios, estado FROM sira.carrera WHERE carrera_id = %s", (carrera_id,))
        carrera = cursor.fetchone()
        cursor.close()
        return carrera
    except HTTPException:
        cursor.close()
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=str(e))

# DELETE
@router.delete("/{carrera_id}")
def eliminar_carrera(carrera_id: int, db=Depends(get_db)):
    cursor = db.cursor()
    try:
        cursor.execute("SELECT carrera_id FROM sira.carrera WHERE carrera_id = %s", (carrera_id,))
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Carrera no encontrada")
        cursor.execute("DELETE FROM sira.carrera WHERE carrera_id = %s", (carrera_id,))
        db.commit()
        cursor.close()
        return {"message": "Carrera eliminada"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=str(e))