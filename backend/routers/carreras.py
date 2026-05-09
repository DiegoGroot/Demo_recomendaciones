from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import get_db
from mysql.connector import errors as mysql_errors
import requests
import fitz  # PyMuPDF
import io
import re

router = APIRouter()

class CarreraCreate(BaseModel):
    nombre: str
    codigo: Optional[str] = None
    descripcion: Optional[str] = None
    duracion_anios: Optional[int] = None

class CarreraUpdate(BaseModel):
    nombre: Optional[str] = None
    codigo: Optional[str] = None
    descripcion: Optional[str] = None
    duracion_anios: Optional[int] = None
    estado: Optional[str] = None

class ImportarMapaSchema(BaseModel):
    url_pdf: str

# GET todas
@router.get("")
def listar_carreras(db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT carrera_id, codigo, nombre, descripcion, duracion_anios, estado, creado_en
            FROM sira.carrera
            ORDER BY nombre
        """)
        result = cursor.fetchall()
        cursor.close()
        return result
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error al listar carreras: {str(e)}")

# GET una
@router.get("/{carrera_id}")
def obtener_carrera(carrera_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT carrera_id, codigo, nombre, descripcion, duracion_anios, estado, creado_en
            FROM sira.carrera WHERE carrera_id = %s
        """, (carrera_id,))
        row = cursor.fetchone()
        cursor.close()
        if not row:
            raise HTTPException(status_code=404, detail="Carrera no encontrada")
        return row
    except HTTPException:
        raise
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=str(e))

# POST crear
@router.post("", status_code=201)
def crear_carrera(data: CarreraCreate, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        codigo = data.codigo
        if not codigo:
            import random
            base = re.sub(r'[^A-Za-z]', '', data.nombre).upper()[:4]
            codigo = f"{base}{random.randint(100,999)}"

        cursor.execute("SELECT carrera_id FROM sira.carrera WHERE nombre = %s", (data.nombre,))
        if cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=409, detail="Ya existe una carrera con ese nombre")

        cursor.execute("""
            INSERT INTO sira.carrera (nombre, codigo, descripcion, duracion_anios, estado)
            VALUES (%s, %s, %s, %s, 'activa')
        """, (data.nombre, codigo, data.descripcion, data.duracion_anios))
        db.commit()
        new_id = cursor.lastrowid
        cursor.execute("SELECT carrera_id, codigo, nombre, descripcion, duracion_anios, estado FROM sira.carrera WHERE carrera_id = %s", (new_id,))
        carrera = cursor.fetchone()
        cursor.close()
        return carrera
    except HTTPException:
        raise
    except mysql_errors.IntegrityError as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=409, detail="Nombre o código de carrera ya registrado")
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error al crear carrera: {str(e)}")

# PUT actualizar
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
        set_clause = ", ".join([f"{k} = %s" for k in campos])
        cursor.execute(
            f"UPDATE sira.carrera SET {set_clause} WHERE carrera_id = %s",
            (*campos.values(), carrera_id)
        )
        db.commit()
        cursor.execute("SELECT carrera_id, codigo, nombre, descripcion, duracion_anios, estado FROM sira.carrera WHERE carrera_id = %s", (carrera_id,))
        carrera = cursor.fetchone()
        cursor.close()
        return carrera
    except HTTPException:
        cursor.close()
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=str(e))

# DELETE
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
        return {"message": "Carrera eliminada"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=str(e))

# ====================================================================
# NUEVO: EXTRAER MATERIAS DESDE LIGA PDF
# ====================================================================
@router.post("/{carrera_id}/importar-mapa")
def importar_mapa_curricular(carrera_id: int, data: ImportarMapaSchema, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        # 1. Verificar que la carrera exista
        cursor.execute("SELECT nombre FROM sira.carrera WHERE carrera_id = %s", (carrera_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Carrera no encontrada")

        # 2. Descargar el PDF desde la liga
        try:
            response = requests.get(data.url_pdf, timeout=15)
            response.raise_for_status()
            pdf_bytes = io.BytesIO(response.content)
        except Exception as e:
            raise HTTPException(status_code=400, detail="No se pudo acceder a la liga del PDF. Verifica que sea pública.")

        # 3. Extraer texto con PyMuPDF
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        texto_completo = ""
        for page in doc:
            texto_completo += page.get_text("text") + "\n"

        # 4. Limpiar y filtrar posibles materias
        lineas = texto_completo.split('\n')
        materias_detectadas = set()
        
        palabras_ignoradas = ["CRÉDITOS", "CREDITOS", "SEMESTRE", "TOTAL", "UNIVERSIDAD", "MAPA", "CURRICULAR", "HORAS", "LICENCIATURA", "ÁREA", "BASICA", "TERMINAL"]
        
        for linea in lineas:
            l = linea.strip()
            # Heurística: más de 5 letras, no es un número solo, menos de 60 letras
            if len(l) > 5 and not l.isdigit() and len(l) < 60:
                if not any(ign in l.upper() for ign in palabras_ignoradas):
                    materias_detectadas.add(l)

        # 5. Insertar en la base de datos
        insertadas = 0
        for mat in list(materias_detectadas):
            nombre_mat = mat.upper()[:100]
            codigo_mat = (re.sub(r'[^A-Z]', '', nombre_mat)[:8] + str(carrera_id)).upper()
            
            # Verificar si ya existe esa materia en la carrera
            cursor.execute("SELECT materia_id FROM sira.materia WHERE codigo = %s OR (nombre = %s AND carrera_id = %s)", 
                           (codigo_mat, nombre_mat, carrera_id))
            
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO sira.materia (nombre, codigo, carrera_id, descripcion, creditos, semestre)
                    VALUES (%s, %s, %s, %s, 5, 1)
                """, (nombre_mat, codigo_mat, carrera_id, "Importada desde liga PDF"))
                insertadas += 1

        db.commit()
        cursor.close()
        return {"message": f"Se procesó el PDF y se agregaron {insertadas} materias exitosamente."}
    
    except HTTPException:
        cursor.close()
        raise
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Error al procesar PDF: {str(e)}")