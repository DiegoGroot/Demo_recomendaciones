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
    creditos: int = 3          # tinyint unsigned NOT NULL → default 3 (debe ser > 0)
    semestre: int = 1          # tinyint unsigned NOT NULL → default 1
    carrera_id: Optional[int] = 1
    contenido: Optional[str] = None

class MateriaUpdate(BaseModel):
    nombre: Optional[str] = None
    codigo: Optional[str] = None
    descripcion: Optional[str] = None
    creditos: Optional[int] = None
    semestre: Optional[int] = None
    carrera_id: Optional[int] = None
    contenido: Optional[str] = None

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
        codigo = data.codigo.strip() if data.codigo and data.codigo.strip() else data.nombre.upper()[:20]

        cursor.execute("SELECT materia_id FROM sira.materia WHERE codigo = %s", (codigo,))
        if cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=409, detail="Ya existe una materia con ese código")

        # creditos y semestre son NOT NULL y deben ser > 0
        creditos = data.creditos if data.creditos is not None and data.creditos > 0 else 3
        semestre = data.semestre if data.semestre is not None and data.semestre > 0 else 1
        
        # Validar restricciones CHECK
        if creditos <= 0:
            raise HTTPException(status_code=400, detail="Los créditos deben ser mayor a 0")
        if semestre <= 0:
            raise HTTPException(status_code=400, detail="El semestre debe ser mayor a 0")

        cursor.execute(
            """INSERT INTO sira.materia
               (nombre, codigo, carrera_id, descripcion, creditos, semestre, contenido)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (data.nombre, codigo, data.carrera_id, data.descripcion or "",
             creditos, semestre, data.contenido)
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
        if "codigo" in str(e).lower():
            raise HTTPException(status_code=409, detail="Ya existe una materia con ese código")
        raise HTTPException(status_code=409, detail=f"Error de integridad: {str(e)}")
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error al crear materia: {str(e)}")

@router.put("/{materia_id}")
def actualizar_materia(materia_id: int, data: MateriaUpdate, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM sira.materia WHERE materia_id = %s", (materia_id,))
        existente = cursor.fetchone()
        if not existente:
            cursor.close()
            raise HTTPException(status_code=404, detail="Materia no encontrada")

        # exclude_unset=True → solo los campos que el cliente envió explícitamente
        enviados = data.model_dump(exclude_unset=True)

        if not enviados:
            cursor.close()
            raise HTTPException(status_code=400, detail="Sin datos para actualizar")

        # creditos y semestre deben ser > 0
        if "creditos" in enviados:
            if enviados["creditos"] is None:
                enviados["creditos"] = existente.get("creditos", 3)
            elif enviados["creditos"] <= 0:
                raise HTTPException(status_code=400, detail="Los créditos deben ser mayor a 0")
                
        if "semestre" in enviados:
            if enviados["semestre"] is None:
                enviados["semestre"] = existente.get("semestre", 1)
            elif enviados["semestre"] <= 0:
                raise HTTPException(status_code=400, detail="El semestre debe ser mayor a 0")

        if "codigo" in enviados and enviados["codigo"]:
            cursor.execute(
                "SELECT materia_id FROM sira.materia WHERE codigo = %s AND materia_id != %s",
                (enviados["codigo"], materia_id)
            )
            if cursor.fetchone():
                cursor.close()
                raise HTTPException(status_code=409, detail="Ya existe una materia con ese código")

        set_parts = [f"{k} = %s" for k in enviados]
        valores = list(enviados.values())
        valores.append(materia_id)

        cursor.execute(
            f"UPDATE sira.materia SET {', '.join(set_parts)} WHERE materia_id = %s",
            tuple(valores)
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
        raise HTTPException(status_code=409, detail=f"Error de integridad: {str(e)}")
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