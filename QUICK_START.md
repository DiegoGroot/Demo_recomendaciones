# 🚀 QUICK START - SIRA

## ⚡ Inicio Rápido (5 minutos)

### 1️⃣ Configurar Base de Datos

```bash
cd /home/diego-groot/Documentos/proyecto_recomendaciones

# Ejecutar el script de configuración
bash setup_database.sh <contraseña_mysql>

# Ejemplo:
bash setup_database.sh root123
```

**Resultado esperado:**
```
✅ Base de datos configurada exitosamente
✅ BD SIRA lista para usar
```

---

### 2️⃣ Iniciar Backend (FastAPI)

```bash
cd backend

# Instalar dependencias (primera vez)
pip install -r requirements.txt

# Iniciar servidor
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Esperado:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

### 3️⃣ Iniciar Frontend (Flutter)

En otra terminal:

```bash
cd flutter_application

# Primera vez (opcional)
flutter pub get

# Iniciar en web
flutter run -d web
```

---

## 📚 Credenciales de Prueba

| Rol | Email | Contraseña | Rol ID |
|-----|-------|-----------|--------|
| **Admin** | admin@sira.com | admin123 | 1 |
| **Tutor** | tutor@sira.com | tutor123 | 2 |
| **Maestro** | maestro@sira.com | maestro123 | 3 |
| **Estudiante** | estudiante@sira.com | estudiante123 | 4 |

---

## 🔌 Endpoints Principales

### Autenticación
- `POST /api/auth/admin/login` - Login Admin
- `POST /api/auth/tutores/login` - Login Tutor
- `POST /api/auth/maestros/login` - Login Maestro
- `POST /api/auth/estudiantes/login` - Login Estudiante

### Recursos
- `GET /api/estudiantes` - Listar estudiantes
- `GET /api/maestros` - Listar maestros
- `GET /api/materias` - Listar materias
- `GET /api/carreras` - Listar carreras
- `GET /api/calificaciones` - Listar calificaciones

### Documentación Interactiva
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🛠️ Estructura de Roles

```
1 = Admin (superAdmin)
2 = Tutor/Coordinador  
3 = Maestro/Docente
4 = Estudiante
```

---

## ⚙️ Crear Nuevo Usuario

### Método 1: MySQL Directo
```sql
-- Crear admin
INSERT INTO usuario (nombre, correo, contrasena, rol_id) 
VALUES ('Nuevo Admin', 'newadmin@sira.com', 'password123', 1);

-- Crear maestro
INSERT INTO maestro (nombre, correo, contrasena, especialidad) 
VALUES ('Nuevo Maestro', 'newmaestro@sira.com', 'password123', 'Matemáticas');

-- Crear estudiante
INSERT INTO estudiante (nombre, correo, contrasena, carrera_id) 
VALUES ('Nuevo Estudiante', 'newest@sira.com', 'password123', 1);
```

### Método 2: API REST
```bash
# Crear estudiante
curl -X POST http://localhost:8000/api/estudiantes \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Juan Pérez",
    "correo": "juan@ejemplo.com",
    "contrasena": "segura123",
    "carrera_id": 1
  }'

# Crear maestro
curl -X POST http://localhost:8000/api/maestros \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Prof. María",
    "correo": "maria@ejemplo.com",
    "contrasena": "segura123",
    "especialidad": "Programación"
  }'
```

---

## 🔍 Validar Sistema

### Verificar BD
```bash
mysql -u root -p
USE sira;
SHOW TABLES;
```

### Verificar Backend
```bash
curl http://localhost:8000/api/health
# Respuesta: {"status":"healthy"}
```

### Verificar Flutter
- Abrir navegador en http://localhost:PORT (que muestre flutter running)

---

## 🆘 Problemas Comunes

### ❌ Error: "Access denied for user 'root'"
**Solución:**
```bash
# Ajustar contraseña o usar sudo
sudo mysql -u root < schema.sql

# O resetear MySQL
sudo mysql -u root -e "GRANT ALL ON *.* TO 'root'@'localhost' IDENTIFIED BY 'root123';"
```

### ❌ Error: "Table 'sira.estudiante' doesn't exist"
**Solución:**
```bash
bash setup_database.sh <contraseña>
```

### ❌ Flutter no conecta con Backend
**Revisar:**
1. Backend está corriendo: `http://localhost:8000/`
2. URL en Flutter correcta: `lib/config/app_config.dart`
3. CORS habilitado en FastAPI ✅

---

## 📱 Funcionalidades Implementadas

✅ **Autenticación por Rol**
- Login diferenciado por tipo de usuario
- Validación de credenciales
- Sistema de roles (1,2,3,4)

✅ **Gestión de Recursos**
- CRUD Estudiantes
- CRUD Maestros  
- CRUD Materias
- CRUD Carreras
- CRUD Calificaciones

✅ **Recomendaciones**
- Sistema automático basado en rendimiento
- Seguimiento de recomendaciones
- Prioridades (alta/media/baja)

---

## 🎯 Próximos Pasos

1. ✅ Loguearse como cada rol
2. ✅ Crear nuevas personas
3. ✅ Verificar datos se guardan en BD
4. Implementar recomendaciones automáticas
5. Agregar gráficos de análisis

---

## 📞 Contacto & Soporte

Para problemas, revisar logs del backend en consola o archivo de configuración.

---

**Última actualización:** 3 de mayo de 2026
**Versión:** 2.0.0
