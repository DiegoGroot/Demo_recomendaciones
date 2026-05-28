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
    contenido: Optional[str] = None
    creditos: int = 3
    semestre: int = 1
    carrera_id: Optional[int] = 1


class MateriaUpdate(BaseModel):
    nombre: Optional[str] = None
    codigo: Optional[str] = None
    descripcion: Optional[str] = None
    contenido: Optional[str] = None
    creditos: Optional[int] = None
    semestre: Optional[int] = None
    carrera_id: Optional[int] = None


def _limpiar_texto(valor: Optional[str]) -> Optional[str]:
    if valor is None:
        return None
    valor = str(valor).strip()
    return valor if valor else None


def _columnas_materia(cursor) -> set:
    """Devuelve las columnas reales de la tabla materia para evitar errores."""
    cursor.execute("""
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'materia'
    """)
    return {row["COLUMN_NAME"] for row in cursor.fetchall()}


@router.get("")
def listar_materias(db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT m.*, c.nombre AS carrera_nombre
            FROM materia m
            LEFT JOIN carrera c ON m.carrera_id = c.carrera_id
            ORDER BY m.semestre, m.nombre
        """)
        result = cursor.fetchall()
        cursor.close()
        return result if result else []
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error al listar materias: {str(e)}")


@router.get("/{materia_id}")
def obtener_materia(materia_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT m.*, c.nombre AS carrera_nombre
            FROM materia m
            LEFT JOIN carrera c ON m.carrera_id = c.carrera_id
            WHERE m.materia_id = %s
        """, (materia_id,))
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
        cols_existentes = _columnas_materia(cursor)

        nombre = _limpiar_texto(data.nombre)
        if not nombre:
            raise HTTPException(status_code=400, detail="El nombre de la materia es obligatorio")

        codigo = _limpiar_texto(data.codigo)
        if not codigo:
            codigo = nombre.upper().replace(" ", "")[:20]

        cursor.execute("SELECT materia_id FROM materia WHERE codigo = %s", (codigo,))
        if cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=409, detail="Ya existe una materia con ese código")

        creditos = data.creditos if data.creditos and data.creditos > 0 else 3
        semestre = data.semestre if data.semestre and data.semestre > 0 else 1

        campos = {
            "nombre": nombre,
            "codigo": codigo,
        }

        if "carrera_id" in cols_existentes:
            campos["carrera_id"] = data.carrera_id or 1
        if "descripcion" in cols_existentes:
            campos["descripcion"] = _limpiar_texto(data.descripcion) or ""
        if "contenido" in cols_existentes:
            campos["contenido"] = _limpiar_texto(data.contenido)
        if "creditos" in cols_existentes:
            campos["creditos"] = creditos
        if "semestre" in cols_existentes:
            campos["semestre"] = semestre

        col_names = ", ".join(campos.keys())
        placeholders = ", ".join(["%s"] * len(campos))

        cursor.execute(
            f"INSERT INTO materia ({col_names}) VALUES ({placeholders})",
            list(campos.values()),
        )
        db.commit()
        id_creada = cursor.lastrowid

        cursor.execute("""
            SELECT m.*, c.nombre AS carrera_nombre
            FROM materia m
            LEFT JOIN carrera c ON m.carrera_id = c.carrera_id
            WHERE m.materia_id = %s
        """, (id_creada,))
        materia = cursor.fetchone()
        cursor.close()
        return materia if materia else {"materia_id": id_creada, "nombre": nombre}
    except HTTPException:
        db.rollback()
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
        cursor.execute("SELECT * FROM materia WHERE materia_id = %s", (materia_id,))
        existente = cursor.fetchone()
        if not existente:
            cursor.close()
            raise HTTPException(status_code=404, detail="Materia no encontrada")

        cols_existentes = _columnas_materia(cursor)
        enviados = data.model_dump(exclude_unset=True)

        if not enviados:
            cursor.close()
            raise HTTPException(status_code=400, detail="Sin datos para actualizar")

        enviados = {k: v for k, v in enviados.items() if k in cols_existentes}

        for key in ["nombre", "codigo", "descripcion", "contenido"]:
            if key in enviados:
                enviados[key] = _limpiar_texto(enviados[key])

        if "nombre" in enviados and not enviados["nombre"]:
            raise HTTPException(status_code=400, detail="El nombre no puede estar vacío")

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
                "SELECT materia_id FROM materia WHERE codigo = %s AND materia_id != %s",
                (enviados["codigo"], materia_id),
            )
            if cursor.fetchone():
                cursor.close()
                raise HTTPException(status_code=409, detail="Ya existe una materia con ese código")

        if not enviados:
            cursor.close()
            raise HTTPException(status_code=400, detail="Sin datos válidos para actualizar")

        set_parts = [f"{k} = %s" for k in enviados]
        valores = list(enviados.values())
        valores.append(materia_id)

        cursor.execute(
            f"UPDATE materia SET {', '.join(set_parts)} WHERE materia_id = %s",
            tuple(valores),
        )
        db.commit()

        cursor.execute("""
            SELECT m.*, c.nombre AS carrera_nombre
            FROM materia m
            LEFT JOIN carrera c ON m.carrera_id = c.carrera_id
            WHERE m.materia_id = %s
        """, (materia_id,))
        materia = cursor.fetchone()
        cursor.close()
        return materia if materia else {"message": "Materia actualizada"}
    except HTTPException:
        db.rollback()
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
        cursor.execute("SELECT materia_id FROM materia WHERE materia_id = %s", (materia_id,))
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Materia no encontrada")
        cursor.execute("DELETE FROM materia WHERE materia_id = %s", (materia_id,))
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
