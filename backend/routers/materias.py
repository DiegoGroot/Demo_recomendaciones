from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import get_db
from mysql.connector import errors as mysql_errors

router = APIRouter()

class MateriaCreate(BaseModel):
    nombre: str
    codigo: Optional[str] = None
    descripcion: Optional[str] = ""
    creditos: int = 3
    semestre: int = 1
    carrera_id: Optional[int] = 1

class MateriaUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    creditos: Optional[int] = None
    semestre: Optional[int] = None

@router.get("")
def listar_materias(db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM sira.materia")
        result = cursor.fetchall()
        cursor.close()
        return result
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error al listar materias: {str(e)}")

@router.get("/{materia_id}")
def obtener_materia(materia_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM sira.materia WHERE materia_id = %s", (materia_id,))
        row = cursor.fetchone()
        cursor.close()
        if not row:
            raise HTTPException(status_code=404, detail="Materia no encontrada")
        return row
    except HTTPException:
        raise
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error al obtener materia: {str(e)}")

@router.post("", status_code=201)
def crear_materia(data: MateriaCreate, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        codigo = data.codigo or data.nombre.upper()[:20]
        cursor.execute("SELECT materia_id FROM sira.materia WHERE codigo = %s", (codigo,))
        if cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=409, detail="Ya existe una materia con ese código")
        
        cursor.execute(
            "INSERT INTO sira.materia (nombre, codigo, carrera_id, descripcion, creditos, semestre) VALUES (%s, %s, %s, %s, %s, %s)",
            (data.nombre, codigo, data.carrera_id, data.descripcion, data.creditos, data.semestre)
        )
        db.commit()
        id_creada = cursor.lastrowid
        cursor.execute("SELECT * FROM sira.materia WHERE materia_id = %s", (id_creada,))
        materia = cursor.fetchone()
        cursor.close()
        return materia if materia else {"materia_id": id_creada, "nombre": data.nombre}
    except HTTPException:
        cursor.close()
        raise
    except mysql_errors.IntegrityError as e:
        db.rollback()
        cursor.close()
        if "codigo" in str(e):
            raise HTTPException(status_code=409, detail="Ya existe una materia con ese código")
        raise HTTPException(status_code=409, detail="Error de integridad: datos duplicados")
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error al crear materia: {str(e)}")

@router.put("/{materia_id}")
def actualizar_materia(materia_id: int, data: MateriaUpdate, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT materia_id FROM sira.materia WHERE materia_id = %s", (materia_id,))
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Materia no encontrada")
        
        campos = {k: v for k, v in data.dict().items() if v is not None}
        if not campos:
            cursor.close()
            raise HTTPException(status_code=400, detail="Sin datos para actualizar")
        
        set_clause = ", ".join([f"{k} = %s" for k in campos])
        cursor.execute(
            f"UPDATE sira.materia SET {set_clause} WHERE materia_id = %s",
            (*campos.values(), materia_id)
        )
        db.commit()
        cursor.execute("SELECT * FROM sira.materia WHERE materia_id = %s", (materia_id,))
        materia = cursor.fetchone()
        cursor.close()
        return materia if materia else {"message": "Materia actualizada"}
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

@router.delete("/{materia_id}")
def eliminar_materia(materia_id: int, db=Depends(get_db)):
    cursor = db.cursor()
    try:
        cursor.execute("SELECT materia_id FROM sira.materia WHERE materia_id = %s", (materia_id,))
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Materia no encontrada")
        
        cursor.execute("DELETE FROM sira.materia WHERE materia_id = %s", (materia_id,))
        db.commit()
        cursor.close()
        return {"message": "Materia eliminada correctamente"}
    except HTTPException:
        cursor.close()
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error al eliminar: {str(e)}")
