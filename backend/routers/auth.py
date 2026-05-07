from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from database import get_db

router = APIRouter(tags=["Auth"])

class LoginRequest(BaseModel):
    correo: str
    contrasena: str

@router.post("/admin/login")
def login_admin(data: LoginRequest, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        # Forzamos búsqueda en tabla 'usuario' (singular)
        query = "SELECT usuario_id, nombre, correo, rol_id FROM usuario WHERE correo = %s AND contrasena = %s AND rol_id = 1"
        cursor.execute(query, (data.correo, data.contrasena))
        user = cursor.fetchone()
        cursor.close()
        
        if not user:
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")
        
        # Devolvemos exactamente lo que Flutter espera
        return {"status": "success", "user": user, "rol": "admin"}
    except Exception as e:
        if 'cursor' in locals(): cursor.close()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/estudiantes/login")
def login_estudiante(data: LoginRequest, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        query = "SELECT estudiante_id, nombre, correo, carrera_id FROM estudiante WHERE correo = %s AND contrasena = %s"
        cursor.execute(query, (data.correo, data.contrasena))
        est = cursor.fetchone()
        cursor.close()
        if not est:
            raise HTTPException(status_code=401, detail="No encontrado")
        return {"status": "success", "estudiante": est, "rol": "estudiante"}
    except Exception as e:
        if 'cursor' in locals(): cursor.close()
        raise HTTPException(status_code=500, detail=str(e))
