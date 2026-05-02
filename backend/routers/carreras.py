from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import get_db
from mysql.connector import errors as mysql_errors

router = APIRouter()

class CarreraCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = ""

class CarreraUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None

@router.get("")
def listar_carreras(db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM sira.carrera")
        result = cursor.fetchall()
        cursor.close()
        return result
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error al listar carreras: {str(e)}")

@router.get("/{carrera_id}")
def obtener_carrera(carrera_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM sira.carrera WHERE carrera_id = %s", (carrera_id,))
        row = cursor.fetchone()
        cursor.close()
        if not row:
            raise HTTPException(status_code=404, detail="Carrera no encontrada")
        return row
    except HTTPException:
        raise
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error al obtener carrera: {str(e)}")

@router.post("", status_code=201)
def crear_carrera(data: CarreraCreate, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT carrera_id FROM sira.carrera WHERE nombre = %s", (data.nombre,))
        if cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=409, detail="Ya existe una carrera con ese nombre")
        
        cursor.execute(
            "INSERT INTO sira.carrera (nombre, descripcion) VALUES (%s, %s)",
            (data.nombre, data.descripcion)
        )
        db.commit()
        id_creada = cursor.lastrowid
        cursor.execute("SELECT * FROM sira.carrera WHERE carrera_id = %s", (id_creada,))
        carrera = cursor.fetchone()
        cursor.close()
        return carrera if carrera else {"carrera_id": id_creada, "nombre": data.nombre, "descripcion": data.descripcion}
    except HTTPException:
        cursor.close()
        raise
    except mysql_errors.IntegrityError as e:
        db.rollback()
        cursor.close()
        if "nombre" in str(e):
            raise HTTPException(status_code=409, detail="Ya existe una carrera con ese nombre")
        raise HTTPException(status_code=409, detail="Error de integridad: datos duplicados")
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error al crear carrera: {str(e)}")

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
        
        if "nombre" in campos:
            cursor.execute(
                "SELECT carrera_id FROM sira.carrera WHERE nombre = %s AND carrera_id != %s",
                (campos["nombre"], carrera_id)
            )
            if cursor.fetchone():
                cursor.close()
                raise HTTPException(status_code=409, detail="Ya existe una carrera con ese nombre")
        
        set_clause = ", ".join([f"{k} = %s" for k in campos])
        cursor.execute(
            f"UPDATE sira.carrera SET {set_clause} WHERE carrera_id = %s",
            (*campos.values(), carrera_id)
        )
        db.commit()
        cursor.execute("SELECT * FROM sira.carrera WHERE carrera_id = %s", (carrera_id,))
        carrera = cursor.fetchone()
        cursor.close()
        return carrera if carrera else {"message": "Carrera actualizada"}
    except HTTPException:
        cursor.close()
        raise
    except mysql_errors.IntegrityError as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=409, detail="Error de integridad: datos duplicados o inválidos")
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error al actualizar: {str(e)}")

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
        return {"message": "Carrera eliminada correctamente"}
    except HTTPException:
        cursor.close()
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error al eliminar: {str(e)}")
