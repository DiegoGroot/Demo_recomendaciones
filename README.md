# SIRA - Sistema de Recomendaciones Académicas Inteligentes

Sistema completo de recomendaciones académicas que integra un backend en Python (FastAPI) con una aplicación móvil en Flutter.

## 📋 Tabla de Contenidos

1. [Requisitos del Sistema](#requisitos-del-sistema)
2. [Instalación](#instalación)
3. [Configuración](#configuración)
4. [Ejecución](#ejecución)
5. [Verificación de Base de Datos](#verificación-de-base-de-datos)
6. [Estructura del Proyecto](#estructura-del-proyecto)
7. [API Endpoints](#api-endpoints)

## 🔧 Requisitos del Sistema

### Backend (Python)
- Python 3.8+
- MySQL Server 5.7+
- pip (gestor de paquetes de Python)

### Frontend (Flutter)
- Flutter SDK (3.0+)
- Dart SDK (incluido con Flutter)
- Android SDK o iOS SDK (según tu plataforma)

### Herramientas Recomendadas
- VS Code con extensiones para Python y Flutter
- MySQL Workbench (para visualizar la base de datos)
- Postman (para probar la API)

## 📦 Instalación

### 1. Clonar o Descargar el Proyecto

```bash
# Si usas git
git clone <tu-repositorio> pruebas
cd pruebas
```

### 2. Configurar Base de Datos MySQL

```bash
# Abre MySQL desde la línea de comandos
mysql -u root -p

# Luego ejecuta el script SQL
source schema.sql

# O si estás fuera de MySQL:
mysql -u root -p < schema.sql
```

### 3. Instalar Dependencias del Backend

```bash
cd backend

# Crear entorno virtual (recomendado)
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate

# En Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 4. Instalar Dependencias de Flutter

```bash
# Desde la raíz del proyecto o en flutter_application
cd flutter_application

# Descargar dependencias
flutter pub get

# Verificar que todo está bien
flutter doctor
```

## ⚙️ Configuración

### Backend - Configurar Variables de Entorno

Crea o modifica el archivo `backend/.env`:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=
DB_NAME=sira
DB_PORT=3306
```

**Importante:** Reemplaza los valores según tu configuración de MySQL.

### Flutter - Configurar URL de API

La URL del API está configurada en `flutter_application/lib/services/api_service.dart`:

```dart
static const String baseUrl = 'http://localhost:8000/api';
```

Si cambias el puerto o la máquina, actualiza esta URL.

## 🚀 Ejecución

### 1. Iniciar el Backend (Python)

```bash
cd backend

# Activar entorno virtual (si no está activo)
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Iniciar el servidor FastAPI
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Salida esperada:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### 2. Verificar Que la API Está Funcionando

Abre en tu navegador:
```
http://localhost:8000/docs
```

Aquí verás la documentación interactiva de Swagger.

### 3. Iniciar la Aplicación Flutter

En otra terminal:

```bash
cd flutter_application

# Para desarrollo
flutter run

# O especificar el dispositivo:
flutter run -d chrome  # Para web
flutter run -d android # Para Android
flutter run -d ios     # Para iOS
```

## 🗄️ Verificación de Base de Datos

### Usar el Script de Gestión

Se incluye un script `backend/db_manager.py` para verificar la base de datos desde terminal:

```bash
cd backend

# Activar entorno virtual
# Windows:
venv\Scripts\activate

# Verificar conexión
python db_manager.py test

# Listar todas las tablas
python db_manager.py tables

# Ver todos los estudiantes
python db_manager.py students

# Ver recomendaciones activas
python db_manager.py recs

# Ver recomendaciones de un estudiante específico
python db_manager.py recs 1

# Ver estadísticas
python db_manager.py stats

# Ver ayuda
python db_manager.py help
```

### Usar MySQL Directamente

```bash
mysql -u root -p
USE sira;

# Ver estudiantes
SELECT * FROM estudiante;

# Ver recomendaciones
SELECT * FROM recomendacion;

# Ver todas las tablas
SHOW TABLES;

# Ver estructura de una tabla
DESCRIBE estudiante;
```

## 📁 Estructura del Proyecto

```
pruebas/
├── backend/
│   ├── main.py                 # Aplicación principal FastAPI
│   ├── database.py             # Configuración de conexión MySQL
│   ├── db_manager.py           # Script para gestionar BD desde terminal
│   ├── requirements.txt         # Dependencias Python
│   ├── .env                    # Variables de entorno
│   └── routers/
│       ├── estudiantes.py      # Endpoints de estudiantes
│       ├── materias.py         # Endpoints de materias
│       ├── calificaciones.py   # Endpoints de calificaciones
│       ├── carreras.py         # Endpoints de carreras
│       └── recomendaciones.py  # Endpoints de recomendaciones
│
├── flutter_application/
│   ├── lib/
│   │   ├── main.dart            # Punto de entrada
│   │   ├── models/
│   │   │   ├── estudiante.dart
│   │   │   ├── materia.dart
│   │   │   ├── carrera.dart
│   │   │   ├── calificacion.dart
│   │   │   └── recomendacion.dart
│   │   ├── screens/
│   │   │   ├── recomendaciones_screen.dart  # Pantalla de recomendaciones
│   │   │   ├── estudiantes_screen.dart
│   │   │   ├── calificaciones_screen.dart
│   │   │   └── materias_screen.dart
│   │   └── services/
│   │       └── api_service.dart # Cliente HTTP para API
│   └── pubspec.yaml            # Dependencias Flutter
│
├── schema.sql                  # Script de base de datos
└── README.md                   # Este archivo
```

## 🔌 API Endpoints

### Recomendaciones (NUEVO)

```
GET    /api/recomendaciones              - Listar todas las recomendaciones
GET    /api/recomendaciones?estudiante_id=1  - Recomendaciones de un estudiante
GET    /api/recomendaciones?prioridad=alta   - Recomendaciones por prioridad
GET    /api/recomendaciones/{id}        - Obtener una recomendación
POST   /api/recomendaciones             - Crear recomendación
PUT    /api/recomendaciones/{id}        - Actualizar recomendación
DELETE /api/recomendaciones/{id}        - Eliminar recomendación
```

### Estudiantes

```
GET    /api/estudiantes                 - Listar estudiantes
GET    /api/estudiantes/{id}            - Obtener estudiante
POST   /api/estudiantes                 - Crear estudiante
PUT    /api/estudiantes/{id}            - Actualizar estudiante
DELETE /api/estudiantes/{id}            - Eliminar estudiante
```

### Materias

```
GET    /api/materias                    - Listar materias
GET    /api/materias/{id}               - Obtener materia
POST   /api/materias                    - Crear materia
PUT    /api/materias/{id}               - Actualizar materia
DELETE /api/materias/{id}               - Eliminar materia
```

### Calificaciones

```
GET    /api/calificaciones              - Listar calificaciones
GET    /api/calificaciones/{id}         - Obtener calificación
POST   /api/calificaciones              - Crear calificación
PUT    /api/calificaciones/{id}         - Actualizar calificación
DELETE /api/calificaciones/{id}         - Eliminar calificación
```

### Carreras

```
GET    /api/carreras                    - Listar carreras
GET    /api/carreras/{id}               - Obtener carrera
POST   /api/carreras                    - Crear carrera
PUT    /api/carreras/{id}               - Actualizar carrera
DELETE /api/carreras/{id}               - Eliminar carrera
```

## 🐛 Solución de Problemas

### Error de Conexión a MySQL

```
❌ Error de conexión: 2003 (HY000): Can't connect to MySQL server
```

**Solución:**
1. Verifica que MySQL está ejecutándose
2. Comprueba las credenciales en `.env`
3. Reinicia el servicio MySQL

### Error de Puerto en Uso

```
ERROR: Application startup failed: Address already in use
```

**Solución:**
```bash
# Matar proceso en puerto 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac:
lsof -i :8000
kill -9 <PID>
```

### Error de Flutter: No puede conectar con API

**Solución:**
1. Verifica que el backend está corriendo (`http://localhost:8000`)
2. En Android/iOS, usa la IP de tu máquina en lugar de `localhost`
3. Desactiva el firewall temporalmente para probar

### Base de Datos Vacía

Si la base de datos no tiene datos, ejecuta nuevamente:

```bash
mysql -u root -p sira < schema.sql
```

## 📚 Documentación de API

Cuando el backend está ejecutándose, accede a:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

Aquí puedes probar todos los endpoints de forma interactiva.

## 🔐 Seguridad

Este proyecto está configurado para desarrollo. Para producción:

1. [ ] Cambiar `allow_origins=["*"]` a dominios específicos
2. [ ] Implementar autenticación JWT
3. [ ] Agregar rate limiting
4. [ ] Usar variables de entorno para credenciales
5. [ ] Habilitar HTTPS

## 📞 Soporte

Para reportar problemas o sugerencias, crea un issue en el repositorio.

---

**Última actualización:** Marzo 2026
**Versión:** 1.0.0
