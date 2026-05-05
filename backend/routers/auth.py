
# backend/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from database import get_db
 
router = APIRouter(tags=["Auth"])
 
class LoginRequest(BaseModel):
    correo: str
    contrasena: str
 
# ============ LOGIN ADMIN (rol_id = 1) ============
@router.post("/admin/login")
def login_admin(data: LoginRequest, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        query = "SELECT usuario_id, nombre, correo, rol_id FROM sira.usuario WHERE correo = %s AND contrasena = %s AND rol_id = 1"
        cursor.execute(query, (data.correo, data.contrasena))
        user = cursor.fetchone()
        cursor.close()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales de administrador incorrectas"
            )
        
        return {"status": "success", "user": user, "rol": "admin"}
    except HTTPException:
        raise
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=str(e))
 
# ============ LOGIN TUTOR (rol_id = 2) ============
@router.post("/tutores/login")
def login_tutor(data: LoginRequest, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        query = "SELECT usuario_id, nombre, correo, rol_id FROM sira.usuario WHERE correo = %s AND contrasena = %s AND rol_id = 2"
        cursor.execute(query, (data.correo, data.contrasena))
        user = cursor.fetchone()
        cursor.close()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales de tutor incorrectas"
            )
        
        return {"status": "success", "user": user, "rol": "tutor"}
    except HTTPException:
        raise
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=str(e))
 
# ============ LOGIN MAESTRO (rol_id = 3) ============
@router.post("/maestros/login")
def login_maestro(data: LoginRequest, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT maestro_id, nombre, correo, especialidad
            FROM sira.maestro
            WHERE correo = %s AND contrasena = %s
        """, (data.correo, data.contrasena))
        maestro = cursor.fetchone()
        cursor.close()
        
        if not maestro:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales de maestro incorrectas"
            )
        
        return {"status": "success", "maestro": maestro, "rol": "maestro"}
    except HTTPException:
        raise
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=str(e))
 
# ============ LOGIN ESTUDIANTE (rol_id = 4) ============
@router.post("/estudiantes/login")
def login_estudiante(data: LoginRequest, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT estudiante_id, nombre, correo, carrera_id
            FROM sira.estudiante
            WHERE correo = %s AND contrasena = %s
        """, (data.correo, data.contrasena))
        estudiante = cursor.fetchone()
        cursor.close()
        
        if not estudiante:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales de estudiante incorrectas"
            )
        
        return {"status": "success", "estudiante": estudiante, "rol": "estudiante"}
    except HTTPException:
        raise
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=str(e))
