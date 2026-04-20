from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from database import get_db
from mysql.connector import errors as mysql_errors

router = APIRouter()

class EstudianteCreate(BaseModel):
    nombre: str
    correo: str
    contrasena: str
    carrera_id: Optional[int] = None

class EstudianteUpdate(BaseModel):
    nombre: Optional[str] = None
    correo: Optional[str] = None
    carrera_id: Optional[int] = None

class LoginData(BaseModel):
    correo: str
    contrasena: str

# GET todos
@router.get("/")
def listar_estudiantes(db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT e.estudiante_id, e.nombre, e.correo, e.carrera_id, c.nombre as carrera, e.creado_en
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
        cursor.execute("""
            SELECT e.estudiante_id, e.nombre, e.correo, e.carrera_id, c.nombre as carrera, e.creado_en
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
@router.post("/", status_code=201)
def crear_estudiante(data: EstudianteCreate, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        # Verificar si el correo ya existe
        cursor.execute("SELECT estudiante_id FROM sira.estudiante WHERE correo = %s", (data.correo,))
        if cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=409, detail="El correo ya está registrado")
        
        # Usar carrera_id por defecto 1 si no se proporciona
        carrera = data.carrera_id if data.carrera_id else 1
        cursor.execute("""
            INSERT INTO sira.estudiante (nombre, correo, contrasena, carrera_id)
            VALUES (%s, %s, %s, %s)
        """, (data.nombre, data.correo, data.contrasena, carrera))
        db.commit()
        # Obtener el estudiante creado
        id_creado = cursor.lastrowid
        cursor.execute("""
            SELECT e.estudiante_id, e.nombre, e.correo, e.carrera_id, c.nombre as carrera, e.creado_en
            FROM sira.estudiante e
            LEFT JOIN sira.carrera c ON e.carrera_id = c.carrera_id
            WHERE e.estudiante_id = %s
        """, (id_creado,))
        estudiante = cursor.fetchone()
        cursor.close()
        return estudiante if estudiante else {"estudiante_id": id_creado, "nombre": data.nombre, "correo": data.correo}
    except mysql_errors.IntegrityError as e:
        db.rollback()
        cursor.close()
        if "Duplicate entry" in str(e) and "correo" in str(e):
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
        # Verificar que el estudiante existe
        cursor.execute("SELECT estudiante_id FROM sira.estudiante WHERE estudiante_id = %s", (estudiante_id,))
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")
        
        campos = {k: v for k, v in data.dict().items() if v is not None}
        if not campos:
            cursor.close()
            raise HTTPException(status_code=400, detail="Sin datos para actualizar")
        
        # Si se está actualizando el correo, verificar que no exista otro con ese correo
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
        # Obtener el estudiante actualizado
        cursor.execute("""
            SELECT e.estudiante_id, e.nombre, e.correo, e.carrera_id, c.nombre as carrera, e.creado_en
            FROM sira.estudiante e
            LEFT JOIN sira.carrera c ON e.carrera_id = c.carrera_id
            WHERE e.estudiante_id = %s
        """, (estudiante_id,))
        estudiante = cursor.fetchone()
        cursor.close()
        return estudiante if estudiante else {"message": "Estudiante actualizado"}
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

# DELETE
@router.delete("/{estudiante_id}")
def eliminar_estudiante(estudiante_id: int, db=Depends(get_db)):
    cursor = db.cursor()
    try:
        # Verificar que el estudiante existe
        cursor.execute("SELECT estudiante_id FROM sira.estudiante WHERE estudiante_id = %s", (estudiante_id,))
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")
        
        # Eliminar el estudiante
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

# LOGIN
@router.post("/login")
def login(data: LoginData, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT estudiante_id, nombre, correo, carrera_id, contrasena
            FROM sira.estudiante
            WHERE correo = %s
        """, (data.correo,))
        user = cursor.fetchone()
        cursor.close()
        if not user:
            raise HTTPException(status_code=401, detail="Correo no encontrado")
        # Verificar contraseña (comparación simple en texto plano)
        if user.get('contrasena') != data.contrasena:
            raise HTTPException(status_code=401, detail="Contraseña incorrecta")
        # Eliminar la contraseña de la respuesta por seguridad
        del user['contrasena']
        return {"message": "Login exitoso", "estudiante": user}
    except HTTPException:
        raise
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error en login: {str(e)}")
