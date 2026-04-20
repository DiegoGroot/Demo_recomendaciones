-- =====================================================
-- SCRIPT DE CREACIÓN DE BASE DE DATOS SIRA
-- Sistema de Recomendaciones Académicas Inteligentes
-- =====================================================

-- Crear base de datos
CREATE DATABASE IF NOT EXISTS sira;
USE sira;

-- =====================================================
-- TABLA: CARRERAS
-- =====================================================
CREATE TABLE IF NOT EXISTS carrera (
    carrera_id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL UNIQUE,
    descripcion TEXT,
    duracion_anos INT DEFAULT 4,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_nombre (nombre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TABLA: ESTUDIANTES
-- =====================================================
CREATE TABLE IF NOT EXISTS estudiante (
    estudiante_id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    correo VARCHAR(100) NOT NULL UNIQUE,
    contrasena VARCHAR(255) NOT NULL,
    carrera_id INT,
    promedio_general DECIMAL(3, 2) DEFAULT 0.00,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (carrera_id) REFERENCES carrera(carrera_id) ON DELETE SET NULL,
    INDEX idx_correo (correo),
    INDEX idx_carrera_id (carrera_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TABLA: MATERIAS
-- =====================================================
CREATE TABLE IF NOT EXISTS materia (
    materia_id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    codigo VARCHAR(50) NOT NULL UNIQUE,
    carrera_id INT NOT NULL,
    creditos INT DEFAULT 3,
    descripcion TEXT,
    semestre INT DEFAULT 1,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (carrera_id) REFERENCES carrera(carrera_id) ON DELETE CASCADE,
    INDEX idx_codigo (codigo),
    INDEX idx_carrera_id (carrera_id),
    INDEX idx_semestre (semestre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TABLA: CALIFICACIONES
-- =====================================================
CREATE TABLE IF NOT EXISTS calificacion (
    calificacion_id INT AUTO_INCREMENT PRIMARY KEY,
    estudiante_id INT NOT NULL,
    materia_id INT NOT NULL,
    nota_parcial1 DECIMAL(3, 2) DEFAULT 0.00,
    nota_parcial2 DECIMAL(3, 2) DEFAULT 0.00,
    nota_final DECIMAL(3, 2) DEFAULT 0.00,
    estado VARCHAR(20) DEFAULT 'en_curso',
    semestre INT,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (estudiante_id) REFERENCES estudiante(estudiante_id) ON DELETE CASCADE,
    FOREIGN KEY (materia_id) REFERENCES materia(materia_id) ON DELETE CASCADE,
    INDEX idx_estudiante_id (estudiante_id),
    INDEX idx_materia_id (materia_id),
    INDEX idx_estado (estado),
    UNIQUE KEY unique_student_subject (estudiante_id, materia_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TABLA: RECOMENDACIONES
-- =====================================================
CREATE TABLE IF NOT EXISTS recomendacion (
    recomendacion_id INT AUTO_INCREMENT PRIMARY KEY,
    estudiante_id INT NOT NULL,
    materia_id INT,
    tipo_recomendacion VARCHAR(50) NOT NULL,
    descripcion TEXT NOT NULL,
    prioridad VARCHAR(20) DEFAULT 'media',
    estado VARCHAR(20) DEFAULT 'activa',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (estudiante_id) REFERENCES estudiante(estudiante_id) ON DELETE CASCADE,
    FOREIGN KEY (materia_id) REFERENCES materia(materia_id) ON DELETE SET NULL,
    INDEX idx_estudiante_id (estudiante_id),
    INDEX idx_tipo_recomendacion (tipo_recomendacion),
    INDEX idx_prioridad (prioridad),
    INDEX idx_estado (estado)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TABLA: AUDITORÍA
-- =====================================================
CREATE TABLE IF NOT EXISTS auditoria (
    auditoria_id INT AUTO_INCREMENT PRIMARY KEY,
    tabla_afectada VARCHAR(100),
    accion VARCHAR(50),
    id_registro INT,
    datos_antiguos JSON,
    datos_nuevos JSON,
    usuario VARCHAR(100),
    fecha_accion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_tabla (tabla_afectada),
    INDEX idx_fecha (fecha_accion)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- DATOS DE EJEMPLO
-- =====================================================

-- Carreras
INSERT INTO carrera (nombre, descripcion, duracion_anos) VALUES
('Ingeniería de Sistemas', 'Carrera de Ingeniería enfocada en sistemas computacionales', 4),
('Administración de Empresas', 'Carrera de ciencias empresariales', 4),
('Psicología', 'Carrera de ciencias de la salud y comportamiento', 5),
('Contabilidad', 'Carrera de ciencias contables y financieras', 4);

-- Estudiantes (ejemplo)
INSERT INTO estudiante (nombre, correo, contrasena, carrera_id, promedio_general) VALUES
('Juan Pérez', 'juan.perez@email.com', 'hash_password_123', 1, 3.8),
('María García', 'maria.garcia@email.com', 'hash_password_456', 2, 3.5),
('Carlos López', 'carlos.lopez@email.com', 'hash_password_789', 1, 3.2);

-- Materias (ejemplo)
INSERT INTO materia (nombre, codigo, carrera_id, creditos, semestre) VALUES
('Programación I', 'PROG101', 1, 4, 1),
('Matemáticas Discretas', 'MAT201', 1, 3, 2),
('Algoritmos', 'PROG202', 1, 4, 2),
('Bases de Datos', 'PROG301', 1, 4, 3),
('Cálculo I', 'MAT101', 2, 3, 1),
('Contabilidad General', 'CONT101', 4, 4, 1);

-- Calificaciones (ejemplo)
INSERT INTO calificacion (estudiante_id, materia_id, nota_parcial1, nota_parcial2, nota_final, estado, semestre) VALUES
(1, 1, 4.0, 3.8, 3.9, 'aprobado', 1),
(1, 2, 3.5, 3.7, 3.6, 'aprobado', 2),
(2, 5, 3.2, 3.4, 3.3, 'aprobado', 1),
(3, 1, 2.8, 2.9, 2.85, 'aprobado', 1);

-- Recomendaciones (ejemplo)
INSERT INTO recomendacion (estudiante_id, materia_id, tipo_recomendacion, descripcion, prioridad, estado) VALUES
(1, 2, 'mejora_academica', 'Considera usar gráficos para visualizar conceptos de matemáticas discretas', 'media', 'activa'),
(2, 5, 'tutoria', 'Se recomienda tutorías en cálculo para fortalecer bases matemáticas', 'alta', 'activa'),
(3, 1, 'recuperacion', 'Necesita refuerzo en conceptos básicos de programación', 'alta', 'activa');

-- =====================================================
-- VISTAS ÚTILES
-- =====================================================

-- Vista para obtener recomendaciones con datos del estudiante
CREATE OR REPLACE VIEW v_recomendaciones_estudiantes AS
SELECT 
    r.recomendacion_id,
    r.estudiante_id,
    e.nombre as estudiante_nombre,
    e.correo,
    r.materia_id,
    m.nombre as materia_nombre,
    m.codigo,
    r.tipo_recomendacion,
    r.descripcion,
    r.prioridad,
    r.estado,
    r.fecha_creacion
FROM recomendacion r
JOIN estudiante e ON r.estudiante_id = e.estudiante_id
LEFT JOIN materia m ON r.materia_id = m.materia_id
ORDER BY r.fecha_creacion DESC;

-- Vista para estadísticas de estudiantes
CREATE OR REPLACE VIEW v_estadisticas_estudiantes AS
SELECT 
    e.estudiante_id,
    e.nombre,
    e.correo,
    c.nombre as carrera,
    COUNT(cal.calificacion_id) as materias_cursadas,
    AVG(cal.nota_final) as promedio_actual,
    COUNT(r.recomendacion_id) as total_recomendaciones,
    SUM(CASE WHEN r.prioridad = 'alta' THEN 1 ELSE 0 END) as recomendaciones_alta_prioridad
FROM estudiante e
LEFT JOIN carrera c ON e.carrera_id = c.carrera_id
LEFT JOIN calificacion cal ON e.estudiante_id = cal.estudiante_id AND cal.estado = 'aprobado'
LEFT JOIN recomendacion r ON e.estudiante_id = r.estudiante_id AND r.estado = 'activa'
GROUP BY e.estudiante_id, e.nombre, e.correo, c.nombre;

-- =====================================================
-- PROCEDIMIENTOS ALMACENADOS (OPCIONAL)
-- =====================================================

-- Procedimiento para obtener recomendaciones por rango de calificación
DROP PROCEDURE IF EXISTS sp_recomendaciones_por_calificacion;
DELIMITER //
CREATE PROCEDURE sp_recomendaciones_por_calificacion(
    IN p_min_cal INT,
    IN p_max_cal INT
)
BEGIN
    SELECT * FROM v_recomendaciones_con_escuela
    WHERE calificacion BETWEEN p_min_cal AND p_max_cal
    ORDER BY calificacion DESC, created_at DESC;
END//
DELIMITER ;

-- Procedimiento para obtener estadísticas de una escuela
DROP PROCEDURE IF EXISTS sp_estadisticas_escuela;
DELIMITER //
CREATE PROCEDURE sp_estadisticas_escuela(
    IN p_escuela_id INT
)
BEGIN
    SELECT * FROM v_estadisticas_escuelas
    WHERE id = p_escuela_id;
END//
DELIMITER ;

-- =====================================================
-- ÍNDICES ADICIONALES PARA OPTIMIZACIÓN
-- =====================================================

-- Los índices principales ya están creados en las tablas.

-- =====================================================
-- COMENTARIOS
-- =====================================================

-- Para ejecutar este script en MySQL:
-- mysql -u root -p < schema.sql
-- 
-- O desde SQLyog/Workbench:
-- 1. Abrir este archivo
-- 2. Ejecutar todo el contenido
-- 3. Verificar que se crean las tablas correctamente