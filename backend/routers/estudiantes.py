from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import get_db
from mysql.connector import errors as mysql_errors

router = APIRouter()

class EstudianteCreate(BaseModel):
    nombre: str
    correo: str
    contrasena: str
    carrera_id: Optional[int] = None
    fecha_nacimiento: Optional[str] = None
    sexo: Optional[str] = None
    nacionalidad: Optional[str] = None
    direccion: Optional[str] = None
    matricula: Optional[str] = None
    modalidad: Optional[str] = None

class EstudianteUpdate(BaseModel):
    nombre: Optional[str] = None
    correo: Optional[str] = None
    carrera_id: Optional[int] = None
    fecha_nacimiento: Optional[str] = None
    sexo: Optional[str] = None
    nacionalidad: Optional[str] = None
    direccion: Optional[str] = None
    matricula: Optional[str] = None
    modalidad: Optional[str] = None

class LoginData(BaseModel):
    correo: str
    contrasena: str

# LOGIN - DEPRECATED
@router.post("/login")
def login(data: LoginData, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT estudiante_id, nombre, correo, carrera_id
            FROM sira.estudiante
            WHERE correo = %s AND contrasena = %s
        """, (data.correo, data.contrasena))
        user = cursor.fetchone()
        cursor.close()
        if not user:
            raise HTTPException(status_code=401, detail="Correo no encontrado")
        return {"message": "Login exitoso", "estudiante": user, "rol": "estudiante"}
    except HTTPException:
        raise
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error en login: {str(e)}")


def _columnas_existentes(cursor) -> set:
    """Retorna el conjunto de columnas que existen actualmente en sira.estudiante."""
    cursor.execute("""
        SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'sira' AND TABLE_NAME = 'estudiante'
    """)
    return {row['COLUMN_NAME'] for row in cursor.fetchall()}


def _build_select(cols: set) -> str:
    """Construye el SELECT dinámicamente según las columnas disponibles."""
    base = "e.estudiante_id, e.nombre, e.correo, e.carrera_id, c.nombre as carrera, e.creado_en"
    opcionales = {
        'fecha_nacimiento': 'e.fecha_nacimiento',
        'sexo': 'e.sexo',
        'nacionalidad': 'e.nacionalidad',
        'direccion': 'e.direccion',
        'matricula': 'e.matricula',
        'modalidad': 'e.modalidad',
        'edad': 'e.edad',
    }
    extras = ", ".join(v for k, v in opcionales.items() if k in cols)
    return f"{base}{', ' + extras if extras else ''}"


# GET todos
@router.get("")
def listar_estudiantes(db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cols = _columnas_existentes(cursor)
        select = _build_select(cols)
        cursor.execute(f"""
            SELECT {select}
            FROM sira.estudiante e
            LEFT JOIN sira.carrera c ON e.carrera_id = c.carrera_id
        """)
        result = cursor.fetchall()
        cursor.close()
        return result
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error al listar estudiantes: {str(e)}")


# GET uno
@router.get("/{estudiante_id}")
def obtener_estudiante(estudiante_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cols = _columnas_existentes(cursor)
        select = _build_select(cols)
        cursor.execute(f"""
            SELECT {select}
            FROM sira.estudiante e
            LEFT JOIN sira.carrera c ON e.carrera_id = c.carrera_id
            WHERE e.estudiante_id = %s
        """, (estudiante_id,))
        row = cursor.fetchone()
        cursor.close()
        if not row:
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")
        return row
    except HTTPException:
        raise
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error al obtener estudiante: {str(e)}")


# POST crear
@router.post("", status_code=201)
def crear_estudiante(data: EstudianteCreate, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT estudiante_id FROM sira.estudiante WHERE correo = %s", (data.correo,))
        if cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=409, detail="El correo ya está registrado")

        cols = _columnas_existentes(cursor)
        carrera = data.carrera_id if data.carrera_id else 1

        # Construir INSERT dinámicamente según columnas disponibles
        campos = {"nombre": data.nombre, "correo": data.correo,
                  "contrasena": data.contrasena, "carrera_id": carrera}
        opcionales = {
            'fecha_nacimiento': data.fecha_nacimiento,
            'sexo': data.sexo,
            'nacionalidad': data.nacionalidad,
            'direccion': data.direccion,
            'matricula': data.matricula,
            'modalidad': data.modalidad,
        }
        for col, val in opcionales.items():
            if col in cols and val is not None:
                campos[col] = val

        col_names = ", ".join(campos.keys())
        placeholders = ", ".join(["%s"] * len(campos))
        cursor.execute(
            f"INSERT INTO sira.estudiante ({col_names}) VALUES ({placeholders})",
            list(campos.values())
        )
        db.commit()
        id_creado = cursor.lastrowid

        select = _build_select(cols)
        cursor.execute(f"""
            SELECT {select}
            FROM sira.estudiante e
            LEFT JOIN sira.carrera c ON e.carrera_id = c.carrera_id
            WHERE e.estudiante_id = %s
        """, (id_creado,))
        estudiante = cursor.fetchone()
        cursor.close()
        return estudiante or {"estudiante_id": id_creado, "nombre": data.nombre, "correo": data.correo}
    except mysql_errors.IntegrityError as e:
        db.rollback()
        cursor.close()
        if "Duplicate entry" in str(e):
            raise HTTPException(status_code=409, detail="El correo ya está registrado")
        raise HTTPException(status_code=400, detail="Error de integridad en los datos")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error al crear estudiante: {str(e)}")


# PUT actualizar
@router.put("/{estudiante_id}")
def actualizar_estudiante(estudiante_id: int, data: EstudianteUpdate, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT estudiante_id FROM sira.estudiante WHERE estudiante_id = %s", (estudiante_id,))
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")

        cols = _columnas_existentes(cursor)

        # Solo incluir campos que existen en la BD
        campos_raw = {k: v for k, v in data.dict().items() if v is not None}
        campos = {k: v for k, v in campos_raw.items() if k in cols}

        if not campos:
            cursor.close()
            raise HTTPException(status_code=400, detail="Sin datos para actualizar")

        if "correo" in campos:
            cursor.execute(
                "SELECT estudiante_id FROM sira.estudiante WHERE correo = %s AND estudiante_id != %s",
                (campos["correo"], estudiante_id)
            )
            if cursor.fetchone():
                cursor.close()
                raise HTTPException(status_code=409, detail="El correo ya está registrado por otro estudiante")

        set_clause = ", ".join([f"{k} = %s" for k in campos])
        cursor.execute(
            f"UPDATE sira.estudiante SET {set_clause} WHERE estudiante_id = %s",
            (*campos.values(), estudiante_id)
        )
        db.commit()

        select = _build_select(cols)
        cursor.execute(f"""
            SELECT {select}
            FROM sira.estudiante e
            LEFT JOIN sira.carrera c ON e.carrera_id = c.carrera_id
            WHERE e.estudiante_id = %s
        """, (estudiante_id,))
        estudiante = cursor.fetchone()
        cursor.close()
        return estudiante or {"message": "Estudiante actualizado"}
    except HTTPException:
        cursor.close()
        raise
    except mysql_errors.IntegrityError:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=409, detail="Error de integridad: datos duplicados o inválidos")
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error al actualizar: {str(e)}")


# DELETE
@router.delete("/{estudiante_id}")
def eliminar_estudiante(estudiante_id: int, db=Depends(get_db)):
    cursor = db.cursor()
    try:
        cursor.execute("SELECT estudiante_id FROM sira.estudiante WHERE estudiante_id = %s", (estudiante_id,))
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")
        cursor.execute("DELETE FROM sira.estudiante WHERE estudiante_id = %s", (estudiante_id,))
        db.commit()
        cursor.close()
        return {"message": "Estudiante eliminado"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error al eliminar: {str(e)}")


# PUT actualizar nombre
@router.put("/{estudiante_id}/nombre")
def actualizar_nombre_estudiante(estudiante_id: int, data: dict, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        if "nombre" not in data or not data["nombre"]:
            cursor.close()
            raise HTTPException(status_code=400, detail="El nombre no puede estar vacío")
        cursor.execute("SELECT estudiante_id FROM sira.estudiante WHERE estudiante_id = %s", (estudiante_id,))
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")
        cursor.execute(
            "UPDATE sira.estudiante SET nombre = %s WHERE estudiante_id = %s",
            (data["nombre"], estudiante_id)
        )
        db.commit()
        cursor.execute(
            "SELECT estudiante_id, nombre, correo, carrera_id FROM sira.estudiante WHERE estudiante_id = %s",
            (estudiante_id,)
        )
        estudiante = cursor.fetchone()
        cursor.close()
        return {"status": "éxito", "mensaje": "Nombre actualizado correctamente", "estudiante": estudiante}
    except HTTPException:
        cursor.close()
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=str(e))


# GET recomendaciones por estudiante
@router.get("/{estudiante_id}/recomendaciones")
def obtener_recomendaciones_estudiante(estudiante_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT r.recomendacion_id, r.estudiante_id, r.materia_id, m.nombre as materia_nombre,
                   r.tipo_recomendacion, r.descripcion, r.prioridad, r.estado,
                   r.fecha_creacion, r.fecha_actualizacion
            FROM sira.recomendacion r
            LEFT JOIN sira.materia m ON r.materia_id = m.materia_id
            WHERE r.estudiante_id = %s
            ORDER BY r.fecha_creacion DESC
        """, (estudiante_id,))
        result = cursor.fetchall()
        cursor.close()
        return result if result else []
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=str(e))


# GET calificaciones por estudiante
@router.get("/{estudiante_id}/calificaciones")
def obtener_calificaciones_estudiante(estudiante_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT c.calificacion_id, c.estudiante_id, c.materia_id, m.nombre as materia_nombre,
                   c.nota_parcial1, c.nota_parcial2, c.nota_parcial3, c.nota_final,
                   c.estado, c.semestre, c.creado_en
            FROM sira.calificacion c
            JOIN sira.materia m ON c.materia_id = m.materia_id
            WHERE c.estudiante_id = %s
            ORDER BY c.creado_en DESC
        """, (estudiante_id,))
        result = cursor.fetchall()
        cursor.close()
        return result if result else []
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=str(e))


# GET evaluaciones por estudiante
@router.get("/{estudiante_id}/evaluaciones")
def obtener_evaluaciones_estudiante(estudiante_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT e.evaluacion_id, e.titulo, e.descripcion, e.estado,
                   ee.completada, ee.calificacion, ee.iniciado_en, ee.completado_en
            FROM sira.evaluacion e
            LEFT JOIN sira.evaluacion_estudiante ee ON e.evaluacion_id = ee.evaluacion_id
                AND ee.estudiante_id = %s
            ORDER BY e.creado_en DESC
        """, (estudiante_id,))
        result = cursor.fetchall()
        cursor.close()
        return result if result else []
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=str(e))


# GET resultados (resumen) del estudiante
@router.get("/{estudiante_id}/resultados")
def obtener_resultados_estudiante(estudiante_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        # Obtener promedio general
        cursor.execute("""
            SELECT AVG(nota_final) as promedio FROM sira.calificacion
            WHERE estudiante_id = %s
        """, (estudiante_id,))
        prom = cursor.fetchone()
        
        # Contar recomendaciones activas
        cursor.execute("""
            SELECT COUNT(*) as total FROM sira.recomendacion
            WHERE estudiante_id = %s AND estado = 'activa'
        """, (estudiante_id,))
        recs = cursor.fetchone()
        
        # Contar evaluaciones completadas
        cursor.execute("""
            SELECT COUNT(*) as total FROM sira.evaluacion_estudiante
            WHERE estudiante_id = %s AND completada = TRUE
        """, (estudiante_id,))
        evals = cursor.fetchone()
        
        cursor.close()
        return {
            "promedio": prom['promedio'],
            "recomendaciones_activas": recs['total'],
            "evaluaciones_completadas": evals['total']
        }
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=str(e))


# POST registro de estudiante
@router.post("/registro")
def registrar_estudiante(data: EstudianteCreate, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        # Verificar que el correo no exista
        cursor.execute("SELECT estudiante_id FROM sira.estudiante WHERE correo = %s", (data.correo,))
        if cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=400, detail="El correo ya está registrado")
        
        # Insertar estudiante
        cursor.execute("""
            INSERT INTO sira.estudiante
            (nombre, correo, contrasena, carrera_id, fecha_nacimiento, sexo,
             nacionalidad, direccion, matricula, modalidad)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (data.nombre, data.correo, data.contrasena, data.carrera_id,
              data.fecha_nacimiento, data.sexo, data.nacionalidad,
              data.direccion, data.matricula, data.modalidad))
        db.commit()
        
        # Obtener el estudiante creado
        cursor.execute("""
            SELECT estudiante_id, nombre, correo, carrera_id
            FROM sira.estudiante WHERE correo = %s
        """, (data.correo,))
        estudiante = cursor.fetchone()
        cursor.close()
        return {"status": "success", "estudiante": estudiante}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=str(e))
        raise HTTPException(status_code=500, detail=f"Error al actualizar nombre: {str(e)}")