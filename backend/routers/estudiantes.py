from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
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
    semestre_actual: Optional[int] = 1
    materias_ids: Optional[List[int]] = None


class EstudianteUpdate(BaseModel):
    nombre: Optional[str] = None
    correo: Optional[str] = None
    contrasena: Optional[str] = None
    carrera_id: Optional[int] = None
    fecha_nacimiento: Optional[str] = None
    sexo: Optional[str] = None
    nacionalidad: Optional[str] = None
    direccion: Optional[str] = None
    matricula: Optional[str] = None
    modalidad: Optional[str] = None
    semestre_actual: Optional[int] = None
    materias_ids: Optional[List[int]] = None


class LoginData(BaseModel):
    correo: str
    contrasena: str


def _columnas_existentes(cursor) -> set:
    cursor.execute("""
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'estudiante'
    """)
    return {row['COLUMN_NAME'] for row in cursor.fetchall()}


def _build_select(cols: set) -> str:
    base = "e.estudiante_id, e.nombre, e.correo, e.carrera_id, c.nombre as carrera, e.creado_en"
    opcionales = {
        'fecha_nacimiento': 'e.fecha_nacimiento',
        'sexo': 'e.sexo',
        'nacionalidad': 'e.nacionalidad',
        'direccion': 'e.direccion',
        'matricula': 'e.matricula',
        'modalidad': 'e.modalidad',
        'edad': 'e.edad',
        'semestre_actual': 'e.semestre_actual',
        'promedio_general': 'e.promedio_general',
        'estado_academico': 'e.estado_academico',
        'codigo_estudiante': 'e.codigo_estudiante',
    }
    extras = ", ".join(v for k, v in opcionales.items() if k in cols)
    return f"{base}{', ' + extras if extras else ''}"


def _columnas_tabla(cursor, tabla: str) -> set:
    cursor.execute("""
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
    """, (tabla,))
    return {row['COLUMN_NAME'] for row in cursor.fetchall()}


def _anio_actual() -> int:
    from datetime import datetime
    return datetime.now().year


def _guardar_inscripciones(cursor, estudiante_id: int, carrera_id: int, semestre_actual: int, materias_ids: Optional[List[int]]):
    """Guarda las materias seleccionadas por el estudiante en la tabla inscripcion.
    Si no llegan materias_ids, no crea inscripciones automáticamente porque el alumno
    debe escoger las materias que realmente cursa.
    """
    if not materias_ids:
        return 0

    # Quitar duplicados conservando orden.
    materias_limpias = []
    vistos = set()
    for mid in materias_ids:
        try:
            mid_int = int(mid)
        except Exception:
            continue
        if mid_int not in vistos:
            materias_limpias.append(mid_int)
            vistos.add(mid_int)

    if not materias_limpias:
        return 0

    placeholders = ", ".join(["%s"] * len(materias_limpias))
    cursor.execute(f"""
        SELECT materia_id, carrera_id, semestre, estado
        FROM sira.materia
        WHERE materia_id IN ({placeholders})
          AND carrera_id = %s
          AND estado = 'activa'
    """, (*materias_limpias, carrera_id))
    materias_validas = cursor.fetchall()
    validas_ids = {int(m['materia_id']) for m in materias_validas}

    invalidas = [mid for mid in materias_limpias if mid not in validas_ids]
    if invalidas:
        raise HTTPException(
            status_code=400,
            detail=f"Las materias {invalidas} no pertenecen a la carrera seleccionada o no están activas"
        )

    cols_inscripcion = _columnas_tabla(cursor, 'inscripcion')
    anio = _anio_actual()
    periodo = 'Actual'
    insertadas = 0

    for materia in materias_validas:
        semestre_materia = int(materia.get('semestre') or semestre_actual or 1)
        campos = {
            'estudiante_id': estudiante_id,
            'materia_id': int(materia['materia_id']),
        }
        if 'semestre_cursado' in cols_inscripcion:
            campos['semestre_cursado'] = semestre_materia
        if 'anio_academico' in cols_inscripcion:
            campos['anio_academico'] = anio
        if 'periodo' in cols_inscripcion:
            campos['periodo'] = periodo
        if 'estado' in cols_inscripcion:
            campos['estado'] = 'activa'

        col_names = ", ".join(campos.keys())
        placeholders_ins = ", ".join(["%s"] * len(campos))
        updates = ", ".join([f"{c}=VALUES({c})" for c in campos.keys() if c not in ('estudiante_id', 'materia_id')])
        sql = f"INSERT INTO sira.inscripcion ({col_names}) VALUES ({placeholders_ins})"
        if updates:
            sql += f" ON DUPLICATE KEY UPDATE {updates}"
        cursor.execute(sql, list(campos.values()))
        insertadas += 1

    return insertadas


def _materias_inscritas(cursor, estudiante_id: int):
    try:
        cursor.execute("""
            SELECT i.inscripcion_id, i.materia_id, m.nombre AS materia_nombre,
                   m.codigo, m.semestre, i.estado
            FROM sira.inscripcion i
            JOIN sira.materia m ON i.materia_id = m.materia_id
            WHERE i.estudiante_id = %s
            ORDER BY m.semestre, m.nombre
        """, (estudiante_id,))
        return cursor.fetchall()
    except Exception:
        return []


def _limpiar_texto(valor: Optional[str]) -> Optional[str]:
    if valor is None:
        return None
    valor = valor.strip()
    return valor if valor else None


def _normalizar_nacionalidades(valor: Optional[str]) -> Optional[str]:
    valor = _limpiar_texto(valor)
    if not valor:
        return None
    partes = []
    vistos = set()
    for parte in valor.split(','):
        n = parte.strip()
        if not n:
            continue
        key = n.lower()
        if key not in vistos:
            partes.append(n)
            vistos.add(key)
    return ", ".join(partes) if partes else None


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
            raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")
        return {"message": "Login exitoso", "estudiante": user, "rol": "estudiante"}
    except HTTPException:
        raise
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error en login: {str(e)}")


# IMPORTANTE: /registro va antes de /{estudiante_id} para que FastAPI no lo confunda con un ID.
@router.post("/registro")
def registrar_estudiante(data: EstudianteCreate, db=Depends(get_db)):
    return crear_estudiante(data, db)


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
            ORDER BY e.nombre ASC
        """)
        result = cursor.fetchall()
        cursor.close()
        return result if result else []
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error al listar estudiantes: {str(e)}")


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

        campos = {
            "nombre": data.nombre.strip(),
            "correo": data.correo.strip(),
            "contrasena": data.contrasena,
            "carrera_id": carrera,
        }

        opcionales = {
            'fecha_nacimiento': _limpiar_texto(data.fecha_nacimiento),
            'sexo': _limpiar_texto(data.sexo),
            'nacionalidad': _normalizar_nacionalidades(data.nacionalidad),
            'direccion': _limpiar_texto(data.direccion),
            'matricula': _limpiar_texto(data.matricula),
            'modalidad': _limpiar_texto(data.modalidad),
            'semestre_actual': data.semestre_actual,
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
        id_creado = cursor.lastrowid

        materias_inscritas_count = _guardar_inscripciones(
            cursor,
            id_creado,
            carrera,
            int(data.semestre_actual or 1),
            data.materias_ids,
        )

        db.commit()

        select = _build_select(cols)
        cursor.execute(f"""
            SELECT {select}
            FROM sira.estudiante e
            LEFT JOIN sira.carrera c ON e.carrera_id = c.carrera_id
            WHERE e.estudiante_id = %s
        """, (id_creado,))
        estudiante = cursor.fetchone()
        if estudiante is not None:
            estudiante['materias_inscritas'] = _materias_inscritas(cursor, id_creado)
            estudiante['materias_inscritas_count'] = materias_inscritas_count
        cursor.close()
        return estudiante or {
            "estudiante_id": id_creado,
            "nombre": data.nombre,
            "correo": data.correo,
            "materias_inscritas_count": materias_inscritas_count,
        }
    except mysql_errors.IntegrityError as e:
        db.rollback()
        cursor.close()
        if "Duplicate entry" in str(e):
            raise HTTPException(status_code=409, detail="Correo o matrícula ya registrados")
        raise HTTPException(status_code=400, detail="Error de integridad en los datos")
    except HTTPException:
        db.rollback()
        try:
            cursor.close()
        except Exception:
            pass
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error al crear estudiante: {str(e)}")


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
        if row:
            row['materias_inscritas'] = _materias_inscritas(cursor, estudiante_id)
        cursor.close()
        if not row:
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")
        return row
    except HTTPException:
        raise
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error al obtener estudiante: {str(e)}")


@router.put("/{estudiante_id}")
def actualizar_estudiante(estudiante_id: int, data: EstudianteUpdate, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT estudiante_id FROM sira.estudiante WHERE estudiante_id = %s", (estudiante_id,))
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")

        cols = _columnas_existentes(cursor)

        raw = data.model_dump(exclude_unset=True)
        materias_ids = raw.pop('materias_ids', None)

        if 'nacionalidad' in raw:
            raw['nacionalidad'] = _normalizar_nacionalidades(raw.get('nacionalidad'))
        for key in ['nombre', 'correo', 'contrasena', 'fecha_nacimiento', 'sexo', 'direccion', 'matricula', 'modalidad']:
            if key in raw:
                raw[key] = _limpiar_texto(raw.get(key))

        # Permite limpiar campos enviando string vacío, pero no actualiza contraseña vacía.
        campos = {}
        for k, v in raw.items():
            if k not in cols:
                continue
            if k == 'contrasena' and not v:
                continue
            campos[k] = v

        if not campos and materias_ids is None:
            cursor.close()
            raise HTTPException(status_code=400, detail="Sin datos para actualizar")

        if "correo" in campos and campos["correo"]:
            cursor.execute(
                "SELECT estudiante_id FROM sira.estudiante WHERE correo = %s AND estudiante_id != %s",
                (campos["correo"], estudiante_id)
            )
            if cursor.fetchone():
                cursor.close()
                raise HTTPException(status_code=409, detail="El correo ya está registrado por otro estudiante")

        if "matricula" in campos and campos["matricula"]:
            cursor.execute(
                "SELECT estudiante_id FROM sira.estudiante WHERE matricula = %s AND estudiante_id != %s",
                (campos["matricula"], estudiante_id)
            )
            if cursor.fetchone():
                cursor.close()
                raise HTTPException(status_code=409, detail="La matrícula ya está registrada por otro estudiante")

        if campos:
            set_clause = ", ".join([f"{k} = %s" for k in campos])
            cursor.execute(
                f"UPDATE sira.estudiante SET {set_clause} WHERE estudiante_id = %s",
                (*campos.values(), estudiante_id)
            )

        # Si se mandan materias desde el formulario, reemplazamos las inscripciones activas
        # de ese estudiante para que coincidan con su selección actual.
        if materias_ids is not None:
            carrera_actual = campos.get('carrera_id')
            semestre_act = campos.get('semestre_actual')
            if carrera_actual is None or semestre_act is None:
                cursor.execute(
                    "SELECT carrera_id, semestre_actual FROM sira.estudiante WHERE estudiante_id = %s",
                    (estudiante_id,)
                )
                row_est = cursor.fetchone() or {}
                carrera_actual = carrera_actual or row_est.get('carrera_id')
                semestre_act = semestre_act or row_est.get('semestre_actual') or 1
            cursor.execute("DELETE FROM sira.inscripcion WHERE estudiante_id = %s", (estudiante_id,))
            _guardar_inscripciones(cursor, estudiante_id, int(carrera_actual), int(semestre_act or 1), materias_ids)

        db.commit()

        select = _build_select(cols)
        cursor.execute(f"""
            SELECT {select}
            FROM sira.estudiante e
            LEFT JOIN sira.carrera c ON e.carrera_id = c.carrera_id
            WHERE e.estudiante_id = %s
        """, (estudiante_id,))
        estudiante = cursor.fetchone()
        if estudiante:
            estudiante['materias_inscritas'] = _materias_inscritas(cursor, estudiante_id)
        cursor.close()
        return estudiante or {"message": "Estudiante actualizado"}
    except HTTPException:
        db.rollback()
        raise
    except mysql_errors.IntegrityError as e:
        db.rollback()
        cursor.close()
        if "Duplicate entry" in str(e):
            raise HTTPException(status_code=409, detail="Correo o matrícula ya registrados")
        raise HTTPException(status_code=409, detail="Error de integridad: datos duplicados o inválidos")
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error al actualizar: {str(e)}")


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


@router.get("/{estudiante_id}/recomendaciones")
def obtener_recomendaciones_estudiante(estudiante_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT r.recomendacion_id, r.estudiante_id, r.materia_id, m.nombre as materia_nombre,
                   r.tipo_recomendacion, r.descripcion, r.prioridad, r.estado,
                   r.fecha_creacion, r.fecha_actualizacion, r.enlace_archivo, r.fecha_limite,
                   r.estrellas_docente, r.retroalimentacion_docente
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


@router.get("/{estudiante_id}/evaluaciones")
def obtener_evaluaciones_estudiante(estudiante_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT e.evaluacion_id, e.titulo, e.descripcion, e.estado,
                   ee.estado as estado_estudiante, ee.fecha_inicio, ee.fecha_fin,
                   ie.respuestas_correctas
            FROM sira.evaluacion e
            JOIN sira.recomendacion r ON e.recomendacion_id = r.recomendacion_id
            LEFT JOIN sira.seguimiento_recomendacion sr
              ON sr.recomendacion_id = r.recomendacion_id
             AND sr.estudiante_id = %s
            LEFT JOIN sira.evaluacion_estudiante ee
              ON ee.evaluacion_id = e.evaluacion_id
             AND ee.seguimiento_id = sr.seguimiento_id
            LEFT JOIN sira.intento_evaluacion ie
              ON ie.evaluacion_estudiante_id = ee.evaluacion_estudiante_id
            WHERE r.estudiante_id = %s
            ORDER BY e.creado_en DESC
        """, (estudiante_id, estudiante_id))
        result = cursor.fetchall()
        cursor.close()
        return result if result else []
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{estudiante_id}/resultados")
def obtener_resultados_estudiante(estudiante_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT AVG(nota_final) as promedio
            FROM sira.calificacion
            WHERE estudiante_id = %s AND nota_final IS NOT NULL
        """, (estudiante_id,))
        prom = cursor.fetchone() or {"promedio": None}

        cursor.execute("""
            SELECT COUNT(*) as total
            FROM sira.recomendacion
            WHERE estudiante_id = %s AND estado = 'activa'
        """, (estudiante_id,))
        recs = cursor.fetchone() or {"total": 0}

        cursor.execute("""
            SELECT COUNT(*) as total
            FROM sira.evaluacion_estudiante ee
            JOIN sira.seguimiento_recomendacion sr ON ee.seguimiento_id = sr.seguimiento_id
            WHERE sr.estudiante_id = %s AND ee.estado = 'finalizada'
        """, (estudiante_id,))
        evals = cursor.fetchone() or {"total": 0}

        cursor.close()
        return {
            "promedio": prom['promedio'],
            "recomendaciones_activas": recs['total'],
            "evaluaciones_completadas": evals['total'],
        }
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=str(e))