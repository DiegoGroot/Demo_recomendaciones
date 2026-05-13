from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import get_db

router = APIRouter()


class LoginData(BaseModel):
    correo: str
    contrasena: str


class RegistroAdminCreate(BaseModel):
    nombre: str
    correo: str
    contrasena: str


class RecuperarBuscarCreate(BaseModel):
    correo: str
    tipo: Optional[str] = None  # 'admin', 'estudiante' o None para buscar en ambos


class RecuperarCambiarCreate(BaseModel):
    correo: str
    nueva_contrasena: str
    tipo: Optional[str] = None  # 'admin', 'estudiante' o None para buscar en ambos


def _limpiar(valor: Optional[str]) -> str:
    return (valor or '').strip()


def _correo(valor: Optional[str]) -> str:
    return _limpiar(valor).lower()


def _asegurar_rol(cursor, nombre: str, descripcion: str) -> int:
    nombre_limpio = _limpiar(nombre).lower()
    cursor.execute(
        "SELECT rol_id FROM sira.rol WHERE LOWER(TRIM(nombre)) = %s LIMIT 1",
        (nombre_limpio,),
    )
    row = cursor.fetchone()
    if row:
        return row['rol_id'] if isinstance(row, dict) else row[0]

    cursor.execute(
        "INSERT INTO sira.rol (nombre, descripcion) VALUES (%s, %s)",
        (nombre_limpio, descripcion),
    )
    return cursor.lastrowid


def _buscar_admin(cursor, correo: str, contrasena: Optional[str] = None):
    params = [correo]
    filtro_pass = ""
    if contrasena is not None:
        filtro_pass = "AND u.contrasena = %s"
        params.append(contrasena)

    cursor.execute(f"""
        SELECT
            u.usuario_id,
            u.nombre,
            u.correo,
            u.rol_id,
            u.estado,
            r.nombre AS rol
        FROM sira.usuario u
        JOIN sira.rol r ON u.rol_id = r.rol_id
        WHERE LOWER(TRIM(u.correo)) = %s
          {filtro_pass}
          AND LOWER(TRIM(r.nombre)) IN ('administrador', 'super_admin', 'admin')
          AND LOWER(TRIM(u.estado)) = 'activo'
        LIMIT 1
    """, tuple(params))
    return cursor.fetchone()


def _buscar_estudiante(cursor, correo: str, contrasena: Optional[str] = None):
    params = [correo]
    filtro_pass = ""
    if contrasena is not None:
        filtro_pass = "AND e.contrasena = %s"
        params.append(contrasena)

    cursor.execute(f"""
        SELECT
            e.estudiante_id,
            e.nombre,
            e.correo,
            e.carrera_id,
            c.nombre AS carrera,
            e.semestre_actual,
            e.sexo,
            e.nacionalidad,
            e.modalidad
        FROM sira.estudiante e
        LEFT JOIN sira.carrera c ON e.carrera_id = c.carrera_id
        WHERE LOWER(TRIM(e.correo)) = %s
          {filtro_pass}
        LIMIT 1
    """, tuple(params))
    return cursor.fetchone()


@router.post('/estudiantes/login')
def login_estudiante(data: LoginData, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        correo = _correo(data.correo)
        contrasena = _limpiar(data.contrasena)

        if not correo or not contrasena:
            raise HTTPException(status_code=400, detail='Correo y contraseña son obligatorios')

        estudiante = _buscar_estudiante(cursor, correo, contrasena)
        cursor.close()

        if not estudiante:
            raise HTTPException(status_code=401, detail='Correo o contraseña incorrectos')

        return {
            'message': 'Login exitoso',
            'rol': 'estudiante',
            'estudiante': estudiante,
            'user': estudiante,
        }
    except HTTPException:
        raise
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f'Error en login de estudiante: {str(e)}')


@router.post('/admin/login')
def login_admin(data: LoginData, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        correo = _correo(data.correo)
        contrasena = _limpiar(data.contrasena)

        if not correo or not contrasena:
            raise HTTPException(status_code=400, detail='Correo y contraseña son obligatorios')

        admin = _buscar_admin(cursor, correo, contrasena)

        if admin:
            cursor.execute(
                "UPDATE sira.usuario SET ultimo_acceso = NOW() WHERE usuario_id = %s",
                (admin['usuario_id'],),
            )
            db.commit()

        cursor.close()

        if not admin:
            raise HTTPException(status_code=401, detail='Correo o contraseña incorrectos')

        # Se devuelven ambos nombres para que funcione con pantallas antiguas y nuevas.
        return {
            'message': 'Login exitoso',
            'rol': 'superAdmin',
            'admin': admin,
            'user': admin,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f'Error en login de admin: {str(e)}')


@router.post('/admin/registro', status_code=201)
def registrar_admin(data: RegistroAdminCreate, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        nombre = _limpiar(data.nombre)
        correo = _correo(data.correo)
        contrasena = _limpiar(data.contrasena)

        if not nombre or not correo or not contrasena:
            raise HTTPException(status_code=400, detail='Nombre, correo y contraseña son obligatorios')

        if len(contrasena) < 4:
            raise HTTPException(status_code=400, detail='La contraseña debe tener al menos 4 caracteres')

        cursor.execute(
            'SELECT usuario_id FROM sira.usuario WHERE LOWER(TRIM(correo)) = %s LIMIT 1',
            (correo,),
        )
        if cursor.fetchone():
            raise HTTPException(status_code=409, detail='El correo ya está registrado como administrador')

        rol_id = _asegurar_rol(cursor, 'administrador', 'Administrador del sistema')
        cursor.execute("""
            INSERT INTO sira.usuario (nombre, correo, contrasena, rol_id, estado)
            VALUES (%s, %s, %s, %s, 'activo')
        """, (nombre, correo, contrasena, rol_id))
        usuario_id = cursor.lastrowid
        db.commit()

        cursor.execute("""
            SELECT u.usuario_id, u.nombre, u.correo, r.nombre AS rol, u.estado
            FROM sira.usuario u
            JOIN sira.rol r ON u.rol_id = r.rol_id
            WHERE u.usuario_id = %s
        """, (usuario_id,))
        admin = cursor.fetchone()
        cursor.close()

        return {
            'message': 'Administrador creado correctamente',
            'rol': 'superAdmin',
            'admin': admin,
            'user': admin,
        }
    except HTTPException:
        db.rollback()
        cursor.close()
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f'Error al registrar admin: {str(e)}')


@router.post('/recuperar/buscar')
def buscar_cuenta_para_recuperar(data: RecuperarBuscarCreate, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        correo = _correo(data.correo)
        tipo = _limpiar(data.tipo).lower()

        if not correo:
            raise HTTPException(status_code=400, detail='Ingresa un correo')

        if tipo in ('admin', 'administrador'):
            admin = _buscar_admin(cursor, correo)
            cursor.close()
            if not admin:
                raise HTTPException(status_code=404, detail='No existe un administrador activo con ese correo')
            return {'existe': True, 'tipo': 'admin', 'nombre': admin['nombre'], 'correo': admin['correo']}

        if tipo == 'estudiante':
            estudiante = _buscar_estudiante(cursor, correo)
            cursor.close()
            if not estudiante:
                raise HTTPException(status_code=404, detail='No existe un estudiante con ese correo')
            return {'existe': True, 'tipo': 'estudiante', 'nombre': estudiante['nombre'], 'correo': estudiante['correo']}

        admin = _buscar_admin(cursor, correo)
        if admin:
            cursor.close()
            return {'existe': True, 'tipo': 'admin', 'nombre': admin['nombre'], 'correo': admin['correo']}

        estudiante = _buscar_estudiante(cursor, correo)
        cursor.close()
        if estudiante:
            return {'existe': True, 'tipo': 'estudiante', 'nombre': estudiante['nombre'], 'correo': estudiante['correo']}

        raise HTTPException(status_code=404, detail='No existe una cuenta con ese correo')
    except HTTPException:
        raise
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f'Error al buscar cuenta: {str(e)}')


@router.post('/recuperar/cambiar')
def cambiar_contrasena_recuperacion(data: RecuperarCambiarCreate, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        correo = _correo(data.correo)
        nueva = _limpiar(data.nueva_contrasena)
        tipo = _limpiar(data.tipo).lower()

        if not correo or not nueva:
            raise HTTPException(status_code=400, detail='Correo y nueva contraseña son obligatorios')

        if len(nueva) < 4:
            raise HTTPException(status_code=400, detail='La contraseña debe tener al menos 4 caracteres')

        if tipo in ('admin', 'administrador'):
            admin = _buscar_admin(cursor, correo)
            if not admin:
                raise HTTPException(status_code=404, detail='No existe un administrador activo con ese correo')
            cursor.execute(
                "UPDATE sira.usuario SET contrasena = %s WHERE usuario_id = %s",
                (nueva, admin['usuario_id']),
            )
            db.commit()
            cursor.close()
            return {'message': 'Contraseña de administrador actualizada', 'tipo': 'admin'}

        if tipo == 'estudiante':
            estudiante = _buscar_estudiante(cursor, correo)
            if not estudiante:
                raise HTTPException(status_code=404, detail='No existe un estudiante con ese correo')
            cursor.execute(
                "UPDATE sira.estudiante SET contrasena = %s WHERE estudiante_id = %s",
                (nueva, estudiante['estudiante_id']),
            )
            db.commit()
            cursor.close()
            return {'message': 'Contraseña de estudiante actualizada', 'tipo': 'estudiante'}

        admin = _buscar_admin(cursor, correo)
        if admin:
            cursor.execute(
                "UPDATE sira.usuario SET contrasena = %s WHERE usuario_id = %s",
                (nueva, admin['usuario_id']),
            )
            db.commit()
            cursor.close()
            return {'message': 'Contraseña de administrador actualizada', 'tipo': 'admin'}

        estudiante = _buscar_estudiante(cursor, correo)
        if estudiante:
            cursor.execute(
                "UPDATE sira.estudiante SET contrasena = %s WHERE estudiante_id = %s",
                (nueva, estudiante['estudiante_id']),
            )
            db.commit()
            cursor.close()
            return {'message': 'Contraseña de estudiante actualizada', 'tipo': 'estudiante'}

        raise HTTPException(status_code=404, detail='No existe una cuenta con ese correo')
    except HTTPException:
        db.rollback()
        cursor.close()
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f'Error al cambiar contraseña: {str(e)}')
