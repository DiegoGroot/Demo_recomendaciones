from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from database import get_db
from auth_utils import hash_password, verify_password
from exceptions import UnauthorizedException, ValidationException

router = APIRouter()

# ── Dependency: valida que el request traiga un token de sesión activo ────────
# Ajusta esta función según cómo manejes sesiones en tu proyecto
# (JWT, cookie, tabla sesion, etc.)
def get_current_admin(x_admin_id: Optional[str] = Header(None), db=Depends(get_db)):
    """
    Valida que el header X-Admin-Id corresponda a un usuario activo con rol admin.
    Úsalo como Depends() en endpoints que sólo los admins deben poder ejecutar.
    """
    if not x_admin_id:
        raise HTTPException(status_code=401, detail="No autenticado: se requiere X-Admin-Id")
    try:
        admin_id = int(x_admin_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Token de sesión inválido")

    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT u.usuario_id, r.nombre AS rol
            FROM usuario u
            JOIN rol r ON u.rol_id = r.rol_id
            WHERE u.usuario_id = %s
              AND LOWER(TRIM(r.nombre)) IN ('administrador', 'super_admin', 'admin')
              AND LOWER(TRIM(u.estado)) = 'activo'
            LIMIT 1
            """,
            (admin_id,),
        )
        admin = cursor.fetchone()
    finally:
        cursor.close()

    if not admin:
        raise HTTPException(status_code=403, detail="Acceso denegado: permisos insuficientes")
    return admin


class LoginData(BaseModel):
    correo: str
    contrasena: str


class RegistroAdminCreate(BaseModel):
    nombre: str
    correo: str
    contrasena: str


class RecuperarBuscarCreate(BaseModel):
    correo: str
    tipo: Optional[str] = None


class RecuperarCambiarCreate(BaseModel):
    correo: str
    nueva_contrasena: str
    tipo: Optional[str] = None


def _limpiar(valor: Optional[str]) -> str:
    return (valor or "").strip()


def _correo(valor: Optional[str]) -> str:
    return _limpiar(valor).lower()


def _password_ok(password: str, stored_password: str) -> bool:
    """
    Verifica contraseña compatible:
    1. Primero intenta bcrypt.
    2. Si el registro antiguo estaba en texto plano, compara directo.
    """
    if not stored_password:
        return False

    if stored_password.startswith("$2a$") or stored_password.startswith("$2b$") or stored_password.startswith("$2y$"):
        return verify_password(password, stored_password)

    return password == stored_password


def _is_bcrypt(stored_password: str) -> bool:
    return bool(stored_password) and (
        stored_password.startswith("$2a$")
        or stored_password.startswith("$2b$")
        or stored_password.startswith("$2y$")
    )


def _asegurar_rol(cursor, nombre: str, descripcion: str) -> int:
    nombre_limpio = _limpiar(nombre).lower()
    cursor.execute(
        "SELECT rol_id FROM rol WHERE LOWER(TRIM(nombre)) = %s LIMIT 1",
        (nombre_limpio,),
    )
    row = cursor.fetchone()
    if row:
        return row["rol_id"] if isinstance(row, dict) else row[0]

    cursor.execute(
        "INSERT INTO rol (nombre, descripcion) VALUES (%s, %s)",
        (nombre_limpio, descripcion),
    )
    return cursor.lastrowid


def _buscar_admin(cursor, correo: str, contrasena: Optional[str] = None):
    cursor.execute(
        """
        SELECT
            u.usuario_id,
            u.nombre,
            u.correo,
            u.contrasena AS hash_contrasena,
            u.rol_id,
            u.estado,
            r.nombre AS rol
        FROM usuario u
        JOIN rol r ON u.rol_id = r.rol_id
        WHERE LOWER(TRIM(u.correo)) = %s
          AND LOWER(TRIM(r.nombre)) IN ('administrador', 'super_admin', 'admin')
          AND LOWER(TRIM(u.estado)) = 'activo'
        LIMIT 1
        """,
        (correo,),
    )

    admin = cursor.fetchone()
    if not admin:
        return None

    if contrasena is not None:
        stored = admin.get("hash_contrasena") if isinstance(admin, dict) else admin[3]
        if not _password_ok(contrasena, stored):
            return None

        # Migración silenciosa: si estaba en texto plano, convertir a bcrypt.
        if not _is_bcrypt(stored):
            nuevo_hash = hash_password(contrasena)
            usuario_id = admin.get("usuario_id") if isinstance(admin, dict) else admin[0]
            cursor.execute(
                "UPDATE usuario SET contrasena = %s WHERE usuario_id = %s",
                (nuevo_hash, usuario_id),
            )

    if isinstance(admin, dict):
        admin.pop("hash_contrasena", None)

    return admin


def _buscar_estudiante(cursor, correo: str, contrasena: Optional[str] = None):
    cursor.execute(
        """
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'estudiante'
        """
    )
    cols_est = {row["COLUMN_NAME"] for row in cursor.fetchall()}

    extras = ""
    for col in [
        "codigo_estudiante",
        "promedio_general",
        "estado_academico",
        "semestre_actual",
        "sexo",
        "nacionalidad",
        "modalidad",
    ]:
        if col in cols_est:
            extras += f", e.{col}"

    cursor.execute(
        f"""
        SELECT
            e.estudiante_id,
            e.nombre,
            e.correo,
            e.contrasena AS hash_contrasena,
            e.carrera_id,
            c.nombre AS carrera
            {extras}
        FROM estudiante e
        LEFT JOIN carrera c ON e.carrera_id = c.carrera_id
        WHERE LOWER(TRIM(e.correo)) = %s
        LIMIT 1
        """,
        (correo,),
    )

    estudiante = cursor.fetchone()
    if not estudiante:
        return None

    if contrasena is not None:
        stored = estudiante.get("hash_contrasena") if isinstance(estudiante, dict) else estudiante[3]
        if not _password_ok(contrasena, stored):
            return None

        # Migración silenciosa: si estaba en texto plano, convertir a bcrypt.
        if not _is_bcrypt(stored):
            nuevo_hash = hash_password(contrasena)
            estudiante_id = estudiante.get("estudiante_id") if isinstance(estudiante, dict) else estudiante[0]
            cursor.execute(
                "UPDATE estudiante SET contrasena = %s WHERE estudiante_id = %s",
                (nuevo_hash, estudiante_id),
            )

    if isinstance(estudiante, dict):
        estudiante.pop("hash_contrasena", None)

    return estudiante


@router.post("/estudiantes/login")
def login_estudiante(data: LoginData, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        correo = _correo(data.correo)
        contrasena = _limpiar(data.contrasena)

        if not correo or not contrasena:
            raise ValidationException("Correo y contraseña son obligatorios")

        estudiante = _buscar_estudiante(cursor, correo, contrasena)

        if not estudiante:
            raise UnauthorizedException("Correo o contraseña incorrectos")

        db.commit()
        cursor.close()

        return {
            "message": "Login exitoso",
            "rol": "estudiante",
            "estudiante": estudiante,
            "user": estudiante,
        }
    except (UnauthorizedException, ValidationException):
        db.rollback()
        cursor.close()
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error en login de estudiante: {str(e)}")


@router.post("/admin/login")
def login_admin(data: LoginData, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        correo = _correo(data.correo)
        contrasena = _limpiar(data.contrasena)

        if not correo or not contrasena:
            raise ValidationException("Correo y contraseña son obligatorios")

        admin = _buscar_admin(cursor, correo, contrasena)

        if not admin:
            raise UnauthorizedException("Correo o contraseña incorrectos")

        cursor.execute(
            "UPDATE usuario SET ultimo_acceso = NOW() WHERE usuario_id = %s",
            (admin["usuario_id"],),
        )

        db.commit()
        cursor.close()

        return {
            "message": "Login exitoso",
            "rol": "superAdmin",
            "admin": admin,
            "user": admin,
        }
    except (UnauthorizedException, ValidationException):
        db.rollback()
        cursor.close()
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error en login de admin: {str(e)}")


@router.post("/admin/registro", status_code=201)
def registrar_admin(data: RegistroAdminCreate, db=Depends(get_db), _: dict = Depends(get_current_admin)):
    cursor = db.cursor(dictionary=True)
    try:
        nombre = _limpiar(data.nombre)
        correo = _correo(data.correo)
        contrasena = _limpiar(data.contrasena)

        if not nombre or not correo or not contrasena:
            raise HTTPException(status_code=400, detail="Nombre, correo y contraseña son obligatorios")
        if len(contrasena) < 4:
            raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 4 caracteres")

        cursor.execute(
            "SELECT usuario_id FROM usuario WHERE LOWER(TRIM(correo)) = %s LIMIT 1",
            (correo,),
        )
        if cursor.fetchone():
            raise HTTPException(status_code=409, detail="El correo ya está registrado como administrador")

        rol_id = _asegurar_rol(cursor, "administrador", "Administrador del sistema")
        contrasena_hash = hash_password(contrasena)

        cursor.execute(
            """
            INSERT INTO usuario (nombre, correo, contrasena, rol_id, estado)
            VALUES (%s, %s, %s, %s, 'activo')
            """,
            (nombre, correo, contrasena_hash, rol_id),
        )
        usuario_id = cursor.lastrowid
        db.commit()

        cursor.execute(
            """
            SELECT u.usuario_id, u.nombre, u.correo, r.nombre AS rol, u.estado
            FROM usuario u
            JOIN rol r ON u.rol_id = r.rol_id
            WHERE u.usuario_id = %s
            """,
            (usuario_id,),
        )
        admin = cursor.fetchone()
        cursor.close()

        return {
            "message": "Administrador creado correctamente",
            "rol": "superAdmin",
            "admin": admin,
            "user": admin,
        }
    except HTTPException:
        db.rollback()
        cursor.close()
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error al registrar admin: {str(e)}")


@router.post("/recuperar/buscar")
def buscar_cuenta_para_recuperar(data: RecuperarBuscarCreate, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        correo = _correo(data.correo)
        tipo = _limpiar(data.tipo).lower()

        if not correo:
            raise HTTPException(status_code=400, detail="Ingresa un correo")

        if tipo in ("admin", "administrador"):
            admin = _buscar_admin(cursor, correo)
            cursor.close()
            if not admin:
                raise HTTPException(status_code=404, detail="No existe un administrador activo con ese correo")
            return {"existe": True, "tipo": "admin", "nombre": admin["nombre"], "correo": admin["correo"]}

        if tipo == "estudiante":
            estudiante = _buscar_estudiante(cursor, correo)
            cursor.close()
            if not estudiante:
                raise HTTPException(status_code=404, detail="No existe un estudiante con ese correo")
            return {"existe": True, "tipo": "estudiante", "nombre": estudiante["nombre"], "correo": estudiante["correo"]}

        admin = _buscar_admin(cursor, correo)
        if admin:
            cursor.close()
            return {"existe": True, "tipo": "admin", "nombre": admin["nombre"], "correo": admin["correo"]}

        estudiante = _buscar_estudiante(cursor, correo)
        cursor.close()
        if estudiante:
            return {"existe": True, "tipo": "estudiante", "nombre": estudiante["nombre"], "correo": estudiante["correo"]}

        raise HTTPException(status_code=404, detail="No existe una cuenta con ese correo")
    except HTTPException:
        raise
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error al buscar cuenta: {str(e)}")


@router.post("/recuperar/cambiar")
def cambiar_contrasena_recuperacion(data: RecuperarCambiarCreate, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        correo = _correo(data.correo)
        nueva = _limpiar(data.nueva_contrasena)
        tipo = _limpiar(data.tipo).lower()

        if not correo or not nueva:
            raise HTTPException(status_code=400, detail="Correo y nueva contraseña son obligatorios")
        if len(nueva) < 4:
            raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 4 caracteres")

        nueva_hash = hash_password(nueva)

        if tipo in ("admin", "administrador"):
            admin = _buscar_admin(cursor, correo)
            if not admin:
                raise HTTPException(status_code=404, detail="No existe un administrador activo con ese correo")
            cursor.execute(
                "UPDATE usuario SET contrasena = %s WHERE usuario_id = %s",
                (nueva_hash, admin["usuario_id"]),
            )
            db.commit()
            cursor.close()
            return {"message": "Contraseña de administrador actualizada", "tipo": "admin"}

        if tipo == "estudiante":
            estudiante = _buscar_estudiante(cursor, correo)
            if not estudiante:
                raise HTTPException(status_code=404, detail="No existe un estudiante con ese correo")
            cursor.execute(
                "UPDATE estudiante SET contrasena = %s WHERE estudiante_id = %s",
                (nueva_hash, estudiante["estudiante_id"]),
            )
            db.commit()
            cursor.close()
            return {"message": "Contraseña de estudiante actualizada", "tipo": "estudiante"}

        admin = _buscar_admin(cursor, correo)
        if admin:
            cursor.execute(
                "UPDATE usuario SET contrasena = %s WHERE usuario_id = %s",
                (nueva_hash, admin["usuario_id"]),
            )
            db.commit()
            cursor.close()
            return {"message": "Contraseña de administrador actualizada", "tipo": "admin"}

        estudiante = _buscar_estudiante(cursor, correo)
        if estudiante:
            cursor.execute(
                "UPDATE estudiante SET contrasena = %s WHERE estudiante_id = %s",
                (nueva_hash, estudiante["estudiante_id"]),
            )
            db.commit()
            cursor.close()
            return {"message": "Contraseña de estudiante actualizada", "tipo": "estudiante"}

        raise HTTPException(status_code=404, detail="No existe una cuenta con ese correo")
    except HTTPException:
        db.rollback()
        cursor.close()
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error al cambiar contraseña: {str(e)}")

# ═══════════════════════════════════════════════════════════════════════════════
# GESTIÓN DE ADMINISTRADORES (solo super_admin puede usar estos endpoints)
# ═══════════════════════════════════════════════════════════════════════════════

class AdminUpdate(BaseModel):
    nombre: Optional[str] = None
    correo: Optional[str] = None

class AdminCambiarContrasena(BaseModel):
    nueva_contrasena: str


@router.get("/admins")
def listar_admins(db=Depends(get_db)):
    """Lista todos los usuarios con rol admin/super_admin."""
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT u.usuario_id, u.nombre, u.correo, u.estado,
                   r.nombre AS rol, u.ultimo_acceso, u.creado_en
            FROM usuario u
            JOIN rol r ON u.rol_id = r.rol_id
            WHERE LOWER(TRIM(r.nombre)) IN ('administrador', 'super_admin', 'admin')
            ORDER BY u.creado_en ASC
        """)
        admins = cursor.fetchall()
        cursor.close()
        # Serializar fechas
        for a in admins:
            for k in ['ultimo_acceso', 'creado_en']:
                if a.get(k):
                    a[k] = str(a[k])
        return admins
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error al listar admins: {str(e)}")


@router.put("/admins/{usuario_id}")
def actualizar_admin(usuario_id: int, data: AdminUpdate, db=Depends(get_db)):
    """Actualiza nombre y/o correo de un administrador."""
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT u.usuario_id FROM usuario u
            JOIN rol r ON u.rol_id = r.rol_id
            WHERE u.usuario_id = %s
              AND LOWER(TRIM(r.nombre)) IN ('administrador', 'super_admin', 'admin')
        """, (usuario_id,))
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Administrador no encontrado")

        campos = {}
        if data.nombre and data.nombre.strip():
            campos['nombre'] = data.nombre.strip()
        if data.correo and data.correo.strip():
            correo = data.correo.strip().lower()
            # Verificar que el correo no esté ya en uso
            cursor.execute(
                "SELECT usuario_id FROM usuario WHERE LOWER(TRIM(correo)) = %s AND usuario_id != %s",
                (correo, usuario_id)
            )
            if cursor.fetchone():
                cursor.close()
                raise HTTPException(status_code=409, detail="El correo ya está en uso por otro usuario")
            campos['correo'] = correo

        if not campos:
            cursor.close()
            raise HTTPException(status_code=400, detail="Sin datos para actualizar")

        set_clause = ", ".join([f"{k} = %s" for k in campos])
        cursor.execute(
            f"UPDATE usuario SET {set_clause} WHERE usuario_id = %s",
            (*campos.values(), usuario_id)
        )
        db.commit()

        cursor.execute("""
            SELECT u.usuario_id, u.nombre, u.correo, u.estado, r.nombre AS rol
            FROM usuario u JOIN rol r ON u.rol_id = r.rol_id
            WHERE u.usuario_id = %s
        """, (usuario_id,))
        admin = cursor.fetchone()
        cursor.close()
        return {"message": "Administrador actualizado", "admin": admin}
    except HTTPException:
        db.rollback()
        cursor.close()
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error al actualizar: {str(e)}")


@router.put("/admins/{usuario_id}/contrasena")
def cambiar_contrasena_admin(usuario_id: int, data: AdminCambiarContrasena, db=Depends(get_db)):
    """Cambia la contraseña de un administrador."""
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT u.usuario_id FROM usuario u
            JOIN rol r ON u.rol_id = r.rol_id
            WHERE u.usuario_id = %s
              AND LOWER(TRIM(r.nombre)) IN ('administrador', 'super_admin', 'admin')
        """, (usuario_id,))
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Administrador no encontrado")

        nueva = data.nueva_contrasena.strip()
        if len(nueva) < 4:
            cursor.close()
            raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 4 caracteres")

        nueva_hash = hash_password(nueva)
        cursor.execute(
            "UPDATE usuario SET contrasena = %s WHERE usuario_id = %s",
            (nueva_hash, usuario_id)
        )
        db.commit()
        cursor.close()
        return {"message": "Contraseña actualizada correctamente"}
    except HTTPException:
        db.rollback()
        cursor.close()
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error al cambiar contraseña: {str(e)}")


@router.delete("/admins/{usuario_id}")
def eliminar_admin(usuario_id: int, db=Depends(get_db)):
    """Elimina un administrador. No se puede eliminar a sí mismo."""
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT u.usuario_id, u.nombre FROM usuario u
            JOIN rol r ON u.rol_id = r.rol_id
            WHERE u.usuario_id = %s
              AND LOWER(TRIM(r.nombre)) IN ('administrador', 'super_admin', 'admin')
        """, (usuario_id,))
        admin = cursor.fetchone()
        if not admin:
            cursor.close()
            raise HTTPException(status_code=404, detail="Administrador no encontrado")

        cursor.execute("DELETE FROM usuario WHERE usuario_id = %s", (usuario_id,))
        db.commit()
        cursor.close()
        return {"message": f"Administrador '{admin['nombre']}' eliminado correctamente"}
    except HTTPException:
        db.rollback()
        cursor.close()
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error al eliminar: {str(e)}")

# ═══════════════════════════════════════════════════════════════════════════════
# GESTIÓN DE ADMINISTRADORES
# ═══════════════════════════════════════════════════════════════════════════════

class AdminUpdate(BaseModel):
    nombre: Optional[str] = None
    correo: Optional[str] = None

class AdminCambiarContrasena(BaseModel):
    nueva_contrasena: str


@router.get("/admins")
def listar_admins(db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT u.usuario_id, u.nombre, u.correo, u.estado,
                   r.nombre AS rol, u.ultimo_acceso, u.creado_en
            FROM usuario u
            JOIN rol r ON u.rol_id = r.rol_id
            WHERE LOWER(TRIM(r.nombre)) IN ('administrador', 'super_admin', 'admin')
            ORDER BY u.creado_en ASC
        """)
        admins = cursor.fetchall()
        cursor.close()
        for a in admins:
            for k in ['ultimo_acceso', 'creado_en']:
                if a.get(k):
                    a[k] = str(a[k])
        return admins
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error al listar admins: {str(e)}")


@router.put("/admins/{usuario_id}")
def actualizar_admin(usuario_id: int, data: AdminUpdate, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT u.usuario_id FROM usuario u
            JOIN rol r ON u.rol_id = r.rol_id
            WHERE u.usuario_id = %s
              AND LOWER(TRIM(r.nombre)) IN ('administrador', 'super_admin', 'admin')
        """, (usuario_id,))
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Administrador no encontrado")

        campos = {}
        if data.nombre and data.nombre.strip():
            campos['nombre'] = data.nombre.strip()
        if data.correo and data.correo.strip():
            correo = data.correo.strip().lower()
            cursor.execute(
                "SELECT usuario_id FROM usuario WHERE LOWER(TRIM(correo)) = %s AND usuario_id != %s",
                (correo, usuario_id)
            )
            if cursor.fetchone():
                cursor.close()
                raise HTTPException(status_code=409, detail="El correo ya está en uso")
            campos['correo'] = correo

        if not campos:
            cursor.close()
            raise HTTPException(status_code=400, detail="Sin datos para actualizar")

        set_clause = ", ".join([f"{k} = %s" for k in campos])
        cursor.execute(
            f"UPDATE usuario SET {set_clause} WHERE usuario_id = %s",
            (*campos.values(), usuario_id)
        )
        db.commit()

        cursor.execute("""
            SELECT u.usuario_id, u.nombre, u.correo, u.estado, r.nombre AS rol
            FROM usuario u JOIN rol r ON u.rol_id = r.rol_id
            WHERE u.usuario_id = %s
        """, (usuario_id,))
        admin = cursor.fetchone()
        cursor.close()
        return {"message": "Administrador actualizado", "admin": admin}
    except HTTPException:
        db.rollback()
        cursor.close()
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error al actualizar: {str(e)}")


@router.put("/admins/{usuario_id}/contrasena")
def cambiar_contrasena_admin(usuario_id: int, data: AdminCambiarContrasena, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT u.usuario_id FROM usuario u
            JOIN rol r ON u.rol_id = r.rol_id
            WHERE u.usuario_id = %s
              AND LOWER(TRIM(r.nombre)) IN ('administrador', 'super_admin', 'admin')
        """, (usuario_id,))
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Administrador no encontrado")

        nueva = data.nueva_contrasena.strip()
        if len(nueva) < 4:
            cursor.close()
            raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 4 caracteres")

        cursor.execute(
            "UPDATE usuario SET contrasena = %s WHERE usuario_id = %s",
            (hash_password(nueva), usuario_id)
        )
        db.commit()
        cursor.close()
        return {"message": "Contraseña actualizada correctamente"}
    except HTTPException:
        db.rollback()
        cursor.close()
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.delete("/admins/{usuario_id}")
def eliminar_admin(usuario_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT u.usuario_id, u.nombre FROM usuario u
            JOIN rol r ON u.rol_id = r.rol_id
            WHERE u.usuario_id = %s
              AND LOWER(TRIM(r.nombre)) IN ('administrador', 'super_admin', 'admin')
        """, (usuario_id,))
        admin = cursor.fetchone()
        if not admin:
            cursor.close()
            raise HTTPException(status_code=404, detail="Administrador no encontrado")

        cursor.execute("DELETE FROM usuario WHERE usuario_id = %s", (usuario_id,))
        db.commit()
        cursor.close()
        return {"message": f"Administrador '{admin['nombre']}' eliminado"}
    except HTTPException:
        db.rollback()
        cursor.close()
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")