from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import get_db
from mysql.connector import errors as mysql_errors

router = APIRouter()

class MaestroCreate(BaseModel):
    nombre: str
    correo: str
    contrasena: str
    especialidad: Optional[str] = None
    fecha_nacimiento: Optional[str] = None
    sexo: Optional[str] = None
    nacionalidad: Optional[str] = None
    direccion: Optional[str] = None

class MaestroUpdate(BaseModel):
    nombre: Optional[str] = None
    correo: Optional[str] = None
    especialidad: Optional[str] = None
    fecha_nacimiento: Optional[str] = None
    sexo: Optional[str] = None
    nacionalidad: Optional[str] = None
    direccion: Optional[str] = None

class LoginData(BaseModel):
    correo: str
    contrasena: str


def _tabla_existe(cursor, tabla: str) -> bool:
    cursor.execute("""
        SELECT COUNT(*) as cnt FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = 'sira' AND TABLE_NAME = %s
    """, (tabla,))
    return cursor.fetchone()['cnt'] > 0


def _columnas_maestro(cursor) -> set:
    cursor.execute("""
        SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'sira' AND TABLE_NAME = 'maestro'
    """)
    return {row['COLUMN_NAME'] for row in cursor.fetchall()}


def _build_select_maestro(cols: set) -> str:
    base = "maestro_id, nombre, correo, especialidad, creado_en"
    opcionales = {
        'fecha_nacimiento': 'fecha_nacimiento',
        'sexo': 'sexo',
        'nacionalidad': 'nacionalidad',
        'direccion': 'direccion',
    }
    extras = ", ".join(v for k, v in opcionales.items() if k in cols)
    return f"{base}{', ' + extras if extras else ''}"


# LOGIN - DEPRECATED
@router.post("/login")
def login_maestro(data: LoginData, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT maestro_id, nombre, correo, especialidad
            FROM sira.maestro WHERE correo = %s AND contrasena = %s
        """, (data.correo, data.contrasena))
        user = cursor.fetchone()
        cursor.close()
        if not user:
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")
        return {"message": "Login exitoso", "maestro": user, "rol": "maestro"}
    except HTTPException:
        raise
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=str(e))


# GET todos los maestros
@router.get("")
def listar_maestros(db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cols = _columnas_maestro(cursor)
        select = _build_select_maestro(cols)
        cursor.execute(f"SELECT {select} FROM sira.maestro")
        result = cursor.fetchall()
        cursor.close()
        return result
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error al listar maestros: {str(e)}")


# GET un maestro
@router.get("/{maestro_id}")
def obtener_maestro(maestro_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cols = _columnas_maestro(cursor)
        select = _build_select_maestro(cols)
        cursor.execute(f"SELECT {select} FROM sira.maestro WHERE maestro_id = %s", (maestro_id,))
        row = cursor.fetchone()
        cursor.close()
        if not row:
            raise HTTPException(status_code=404, detail="Maestro no encontrado")
        return row
    except HTTPException:
        raise
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=str(e))


# POST crear maestro
@router.post("", status_code=201)
def crear_maestro(data: MaestroCreate, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT maestro_id FROM sira.maestro WHERE correo = %s", (data.correo,))
        if cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=409, detail="El correo ya está registrado")

        cols = _columnas_maestro(cursor)
        campos = {"nombre": data.nombre, "correo": data.correo,
                  "contrasena": data.contrasena, "especialidad": data.especialidad}
        opcionales = {
            'fecha_nacimiento': data.fecha_nacimiento,
            'sexo': data.sexo,
            'nacionalidad': data.nacionalidad,
            'direccion': data.direccion,
        }
        for col, val in opcionales.items():
            if col in cols and val is not None:
                campos[col] = val

        col_names = ", ".join(campos.keys())
        placeholders = ", ".join(["%s"] * len(campos))
        cursor.execute(
            f"INSERT INTO sira.maestro ({col_names}) VALUES ({placeholders})",
            list(campos.values())
        )
        db.commit()
        new_id = cursor.lastrowid
        select = _build_select_maestro(cols)
        cursor.execute(f"SELECT {select} FROM sira.maestro WHERE maestro_id = %s", (new_id,))
        maestro = cursor.fetchone()
        cursor.close()
        return maestro
    except HTTPException:
        raise
    except mysql_errors.IntegrityError:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=409, detail="El correo ya está registrado")
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=str(e))


# PUT actualizar maestro
@router.put("/{maestro_id}")
def actualizar_maestro(maestro_id: int, data: MaestroUpdate, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT maestro_id FROM sira.maestro WHERE maestro_id = %s", (maestro_id,))
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Maestro no encontrado")

        cols = _columnas_maestro(cursor)
        campos_raw = {k: v for k, v in data.dict().items() if v is not None}
        campos = {k: v for k, v in campos_raw.items() if k in cols}

        if not campos:
            cursor.close()
            raise HTTPException(status_code=400, detail="Sin datos para actualizar")

        set_clause = ", ".join([f"{k} = %s" for k in campos])
        cursor.execute(
            f"UPDATE sira.maestro SET {set_clause} WHERE maestro_id = %s",
            (*campos.values(), maestro_id)
        )
        db.commit()
        select = _build_select_maestro(cols)
        cursor.execute(f"SELECT {select} FROM sira.maestro WHERE maestro_id = %s", (maestro_id,))
        maestro = cursor.fetchone()
        cursor.close()
        return maestro
    except HTTPException:
        cursor.close()
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=str(e))


# DELETE maestro
@router.delete("/{maestro_id}")
def eliminar_maestro(maestro_id: int, db=Depends(get_db)):
    cursor = db.cursor()
    try:
        cursor.execute("SELECT maestro_id FROM sira.maestro WHERE maestro_id = %s", (maestro_id,))
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Maestro no encontrado")
        cursor.execute("DELETE FROM sira.maestro WHERE maestro_id = %s", (maestro_id,))
        db.commit()
        cursor.close()
        return {"message": "Maestro eliminado"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=str(e))


# GET materias del maestro
@router.get("/{maestro_id}/materias")
def materias_del_maestro(maestro_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        if not _tabla_existe(cursor, 'materia_maestro'):
            cursor.close()
            return []  # tabla aún no migrada — devolver lista vacía sin error
        cursor.execute("""
            SELECT m.materia_id, m.nombre, m.codigo, m.creditos, m.semestre,
                   c.nombre as carrera_nombre
            FROM sira.materia_maestro mm
            JOIN sira.materia m ON mm.materia_id = m.materia_id
            LEFT JOIN sira.carrera c ON m.carrera_id = c.carrera_id
            WHERE mm.maestro_id = %s
        """, (maestro_id,))
        result = cursor.fetchall()
        cursor.close()
        return result
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=str(e))


# POST asignar materia a maestro
@router.post("/{maestro_id}/materias/{materia_id}")
def asignar_materia(maestro_id: int, materia_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        if not _tabla_existe(cursor, 'materia_maestro'):
            # Crear la tabla al vuelo si no existe
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sira.materia_maestro (
                    maestro_id INT NOT NULL,
                    materia_id INT NOT NULL,
                    PRIMARY KEY (maestro_id, materia_id),
                    FOREIGN KEY (maestro_id) REFERENCES sira.maestro(maestro_id) ON DELETE CASCADE,
                    FOREIGN KEY (materia_id) REFERENCES sira.materia(materia_id) ON DELETE CASCADE
                )
            """)
            db.commit()
        cursor.execute("""
            INSERT IGNORE INTO sira.materia_maestro (maestro_id, materia_id)
            VALUES (%s, %s)
        """, (maestro_id, materia_id))
        db.commit()
        cursor.close()
        return {"message": "Materia asignada"}
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=str(e))


# DELETE quitar materia de maestro
@router.delete("/{maestro_id}/materias/{materia_id}")
def quitar_materia(maestro_id: int, materia_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        if not _tabla_existe(cursor, 'materia_maestro'):
            cursor.close()
            return {"message": "Materia removida"}
        cursor.execute("""
            DELETE FROM sira.materia_maestro
            WHERE maestro_id = %s AND materia_id = %s
        """, (maestro_id, materia_id))
        db.commit()
        cursor.close()
        return {"message": "Materia removida"}
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=str(e))


# GET estudiantes de una materia del maestro
@router.get("/{maestro_id}/materias/{materia_id}/estudiantes")
def estudiantes_de_materia_maestro(maestro_id: int, materia_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT e.estudiante_id, e.nombre, e.correo,
                   cal.calificacion_id,
                   cal.nota_parcial1, cal.nota_parcial2, cal.nota_final, cal.estado,
                   r.recomendacion_id,
                   r.descripcion as recomendacion,
                   r.prioridad, r.tipo_recomendacion, r.estado as rec_estado
            FROM sira.calificacion cal
            JOIN sira.estudiante e ON cal.estudiante_id = e.estudiante_id
            LEFT JOIN sira.recomendacion r ON r.estudiante_id = e.estudiante_id
                AND r.materia_id = %s AND r.estado = 'activa'
            WHERE cal.materia_id = %s
            ORDER BY e.nombre
        """, (materia_id, materia_id))
        result = cursor.fetchall()
        cursor.close()
        return result
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=str(e))