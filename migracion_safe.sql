USE sira;

-- Procedimiento para agregar columna solo si no existe
DROP PROCEDURE IF EXISTS agregar_columna;

DELIMITER $$
CREATE PROCEDURE agregar_columna(
    IN p_tabla VARCHAR(64),
    IN p_columna VARCHAR(64),
    IN p_definicion VARCHAR(200)
)
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'sira'
          AND TABLE_NAME = p_tabla
          AND COLUMN_NAME = p_columna
    ) THEN
        SET @sql = CONCAT('ALTER TABLE sira.', p_tabla, ' ADD COLUMN ', p_columna, ' ', p_definicion);
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
END$$
DELIMITER ;

-- ── Columnas de estudiante ────────────────────────────────────
CALL agregar_columna('estudiante', 'fecha_nacimiento', 'DATE NULL');
CALL agregar_columna('estudiante', 'sexo',             'VARCHAR(20) NULL');
CALL agregar_columna('estudiante', 'nacionalidad',     'VARCHAR(60) NULL');
CALL agregar_columna('estudiante', 'direccion',        'VARCHAR(200) NULL');
CALL agregar_columna('estudiante', 'matricula',        'VARCHAR(30) NULL');
CALL agregar_columna('estudiante', 'modalidad',        'VARCHAR(30) NULL');
CALL agregar_columna('estudiante', 'edad',             'INT NULL');

-- ── Columnas de maestro ───────────────────────────────────────
CALL agregar_columna('maestro', 'fecha_nacimiento', 'DATE NULL');
CALL agregar_columna('maestro', 'sexo',             'VARCHAR(20) NULL');
CALL agregar_columna('maestro', 'nacionalidad',     'VARCHAR(60) NULL');
CALL agregar_columna('maestro', 'direccion',        'VARCHAR(200) NULL');

-- ── Tabla materia_maestro (con INT UNSIGNED) ──────────────────
CREATE TABLE IF NOT EXISTS materia_maestro (
    maestro_id  INT UNSIGNED NOT NULL,
    materia_id  INT UNSIGNED NOT NULL,
    PRIMARY KEY (maestro_id, materia_id),
    FOREIGN KEY (maestro_id) REFERENCES maestro(maestro_id) ON DELETE CASCADE,
    FOREIGN KEY (materia_id) REFERENCES materia(materia_id) ON DELETE CASCADE
);

DROP PROCEDURE IF EXISTS agregar_columna;

-- ================================================================
-- SIRA - Tablas del sistema de Evaluaciones
-- Ejecuta esto en tu BD si las tablas no existen todavía
-- ================================================================

-- Tabla principal de evaluaciones (vinculada a recomendaciones)
CREATE TABLE IF NOT EXISTS sira.evaluacion (
    evaluacion_id INT AUTO_INCREMENT PRIMARY KEY,
    recomendacion_id INT NOT NULL,
    titulo VARCHAR(255) NOT NULL,
    descripcion TEXT,
    estado ENUM('activa', 'cerrada') DEFAULT 'activa',
    creado_en DATETIME DEFAULT NOW(),
    FOREIGN KEY (recomendacion_id) REFERENCES sira.recomendacion(recomendacion_id)
        ON DELETE CASCADE
);

-- Preguntas de cada evaluación
CREATE TABLE IF NOT EXISTS sira.pregunta (
    pregunta_id INT AUTO_INCREMENT PRIMARY KEY,
    evaluacion_id INT NOT NULL,
    texto_pregunta TEXT NOT NULL,
    tipo_pregunta ENUM('abierta', 'opcion_multiple', 'si_no', 'escala') DEFAULT 'abierta',
    orden INT DEFAULT 1,
    requerida BOOLEAN DEFAULT TRUE,
    creado_en DATETIME DEFAULT NOW(),
    FOREIGN KEY (evaluacion_id) REFERENCES sira.evaluacion(evaluacion_id)
        ON DELETE CASCADE
);

-- Opciones de respuesta (para preguntas tipo opcion_multiple y si_no)
CREATE TABLE IF NOT EXISTS sira.opcion_respuesta (
    opcion_id INT AUTO_INCREMENT PRIMARY KEY,
    pregunta_id INT NOT NULL,
    texto_opcion VARCHAR(500) NOT NULL,
    es_correcta BOOLEAN DEFAULT FALSE,
    orden INT DEFAULT 1,
    creado_en DATETIME DEFAULT NOW(),
    FOREIGN KEY (pregunta_id) REFERENCES sira.pregunta(pregunta_id)
        ON DELETE CASCADE
);

-- Registro de intento del estudiante (una fila por estudiante+evaluacion)
CREATE TABLE IF NOT EXISTS sira.evaluacion_estudiante (
    ee_id INT AUTO_INCREMENT PRIMARY KEY,
    evaluacion_id INT NOT NULL,
    estudiante_id INT NOT NULL,
    completada BOOLEAN DEFAULT FALSE,
    calificacion DECIMAL(5,2) DEFAULT NULL,
    iniciado_en DATETIME DEFAULT NOW(),
    completado_en DATETIME DEFAULT NULL,
    FOREIGN KEY (evaluacion_id) REFERENCES sira.evaluacion(evaluacion_id)
        ON DELETE CASCADE,
    FOREIGN KEY (estudiante_id) REFERENCES sira.estudiante(estudiante_id)
        ON DELETE CASCADE
);

-- Respuestas individuales del estudiante por pregunta
CREATE TABLE IF NOT EXISTS sira.respuesta_estudiante (
    respuesta_id INT AUTO_INCREMENT PRIMARY KEY,
    evaluacion_estudiante_id INT NOT NULL,
    pregunta_id INT NOT NULL,
    texto_respuesta TEXT DEFAULT NULL,
    opcion_id INT DEFAULT NULL,
    respondido_en DATETIME DEFAULT NOW(),
    FOREIGN KEY (evaluacion_estudiante_id)
        REFERENCES sira.evaluacion_estudiante(ee_id) ON DELETE CASCADE,
    FOREIGN KEY (pregunta_id)
        REFERENCES sira.pregunta(pregunta_id) ON DELETE CASCADE,
    FOREIGN KEY (opcion_id)
        REFERENCES sira.opcion_respuesta(opcion_id) ON DELETE SET NULL
);

SELECT 'Migración completada ✅' AS resultado;

