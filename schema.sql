-- ==========================================================
-- SIRA / proyecto_recomendaciones
-- Rediseño de base de datos MySQL
-- Compatible con FastAPI + Flutter
-- ==========================================================

SET NAMES utf8mb4;
SET time_zone = '+00:00';

CREATE DATABASE IF NOT EXISTS sira
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE sira;

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS respuesta_estudiante;
DROP TABLE IF EXISTS intento_evaluacion;
DROP TABLE IF EXISTS evaluacion_estudiante;
DROP TABLE IF EXISTS opcion_respuesta;
DROP TABLE IF EXISTS pregunta;
DROP TABLE IF EXISTS evaluacion;
DROP TABLE IF EXISTS interaccion_contenido;
DROP TABLE IF EXISTS seguimiento_recomendacion;
DROP TABLE IF EXISTS recomendacion;
DROP TABLE IF EXISTS calificacion;
DROP TABLE IF EXISTS nivel_rendimiento;
DROP TABLE IF EXISTS inscripcion;
DROP TABLE IF EXISTS estudiante;
DROP TABLE IF EXISTS maestro;
DROP TABLE IF EXISTS materia;
DROP TABLE IF EXISTS plan_estudio;
DROP TABLE IF EXISTS carrera;
DROP TABLE IF EXISTS usuario;
DROP TABLE IF EXISTS rol;
DROP TABLE IF EXISTS respuesta_personal;

SET FOREIGN_KEY_CHECKS = 1;

-- ==========================================================
-- TABLAS MAESTRAS
-- ==========================================================

CREATE TABLE rol (
  rol_id TINYINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(30) NOT NULL,
  descripcion VARCHAR(255) NULL,
  creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_rol_nombre (nombre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE usuario (
  usuario_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(120) NOT NULL,
  correo VARCHAR(140) NOT NULL,
  contrasena VARCHAR(255) NOT NULL,
  rol_id TINYINT UNSIGNED NOT NULL,
  estado ENUM('activo','inactivo','bloqueado') NOT NULL DEFAULT 'activo',
  ultimo_acceso DATETIME NULL,
  creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_usuario_correo (correo),
  KEY idx_usuario_rol (rol_id),
  CONSTRAINT fk_usuario_rol
    FOREIGN KEY (rol_id) REFERENCES rol(rol_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE carrera (
  carrera_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  codigo VARCHAR(20) NOT NULL DEFAULT '',
  nombre VARCHAR(120) NOT NULL,
  descripcion VARCHAR(240) NULL,
  duracion_anios TINYINT UNSIGNED NULL,
  estado ENUM('activa','inactiva') NOT NULL DEFAULT 'activa',
  creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_carrera_codigo (codigo),
  UNIQUE KEY uk_carrera_nombre (nombre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE maestro (
  maestro_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(120) NOT NULL,
  correo VARCHAR(140) NOT NULL,
  contrasena VARCHAR(255) NOT NULL,
  especialidad VARCHAR(120) NULL,
  creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_maestro_correo (correo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE plan_estudio (
  plan_estudio_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  carrera_id INT UNSIGNED NOT NULL,
  nombre VARCHAR(140) NOT NULL,
  version VARCHAR(20) NOT NULL DEFAULT '1.0',
  descripcion VARCHAR(255) NULL,
  vigente BOOLEAN NOT NULL DEFAULT TRUE,
  creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_plan_estudio (carrera_id, nombre, version),
  KEY idx_plan_estudio_carrera (carrera_id),
  CONSTRAINT fk_plan_estudio_carrera
    FOREIGN KEY (carrera_id) REFERENCES carrera(carrera_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE materia (
  materia_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  carrera_id INT UNSIGNED NOT NULL,
  plan_estudio_id INT UNSIGNED NULL,
  codigo VARCHAR(20) NOT NULL,
  nombre VARCHAR(140) NOT NULL,
  descripcion VARCHAR(255) NULL,
  creditos TINYINT UNSIGNED NOT NULL,
  semestre TINYINT UNSIGNED NOT NULL,
  estado ENUM('activa','inactiva') NOT NULL DEFAULT 'activa',
  creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_materia_codigo (codigo),
  UNIQUE KEY uk_materia_carrera_nombre (carrera_id, nombre),
  KEY idx_materia_carrera (carrera_id),
  KEY idx_materia_plan_estudio (plan_estudio_id),
  KEY idx_materia_semestre (semestre),
  CONSTRAINT fk_materia_carrera
    FOREIGN KEY (carrera_id) REFERENCES carrera(carrera_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  CONSTRAINT fk_materia_plan_estudio
    FOREIGN KEY (plan_estudio_id) REFERENCES plan_estudio(plan_estudio_id)
    ON UPDATE CASCADE
    ON DELETE SET NULL,
  CONSTRAINT chk_materia_creditos CHECK (creditos > 0),
  CONSTRAINT chk_materia_semestre CHECK (semestre > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE estudiante (
  estudiante_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  usuario_id INT UNSIGNED NULL,
  nombre VARCHAR(120) NOT NULL,
  correo VARCHAR(140) NOT NULL,
  contrasena VARCHAR(255) NOT NULL,
  carrera_id INT UNSIGNED NOT NULL,
  codigo_estudiante VARCHAR(30) NULL,
  promedio_general DECIMAL(4,2) NOT NULL DEFAULT 0.00,
  estado_academico ENUM('sin_calificar','riesgo','regular','bueno','excelente') NOT NULL DEFAULT 'sin_calificar',
  edad TINYINT UNSIGNED NULL,
  fecha_nacimiento DATE NULL,
  creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_estudiante_correo (correo),
  UNIQUE KEY uk_estudiante_codigo (codigo_estudiante),
  UNIQUE KEY uk_estudiante_usuario (usuario_id),
  KEY idx_estudiante_carrera (carrera_id),
  CONSTRAINT fk_estudiante_usuario
    FOREIGN KEY (usuario_id) REFERENCES usuario(usuario_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  CONSTRAINT fk_estudiante_carrera
    FOREIGN KEY (carrera_id) REFERENCES carrera(carrera_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  CONSTRAINT chk_estudiante_promedio CHECK (promedio_general BETWEEN 0 AND 5)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE nivel_rendimiento (
  nivel_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(60) NOT NULL,
  rango_min DECIMAL(4,2) NOT NULL,
  rango_max DECIMAL(4,2) NOT NULL,
  descripcion VARCHAR(255) NULL,
  creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_nivel_nombre (nombre),
  CONSTRAINT chk_nivel_rango CHECK (rango_min <= rango_max)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==========================================================
-- TABLAS TRANSACCIONALES ACADÉMICAS
-- ==========================================================

CREATE TABLE inscripcion (
  inscripcion_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  estudiante_id INT UNSIGNED NOT NULL,
  materia_id INT UNSIGNED NOT NULL,
  semestre_cursado TINYINT UNSIGNED NOT NULL,
  anio_academico SMALLINT UNSIGNED NULL,
  periodo VARCHAR(20) NULL,
  fecha_inscripcion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  estado ENUM('activa','aprobada','reprobada','retirada') NOT NULL DEFAULT 'activa',
  creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_inscripcion_unica (estudiante_id, materia_id, semestre_cursado, anio_academico),
  KEY idx_inscripcion_estudiante (estudiante_id),
  KEY idx_inscripcion_materia (materia_id),
  CONSTRAINT fk_inscripcion_estudiante
    FOREIGN KEY (estudiante_id) REFERENCES estudiante(estudiante_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT fk_inscripcion_materia
    FOREIGN KEY (materia_id) REFERENCES materia(materia_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  CONSTRAINT chk_inscripcion_semestre CHECK (semestre_cursado > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE calificacion (
  calificacion_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  inscripcion_id INT UNSIGNED NOT NULL,
  estudiante_id INT UNSIGNED NOT NULL,
  materia_id INT UNSIGNED NOT NULL,
  nota_parcial1 DECIMAL(4,2) NULL,
  nota_parcial2 DECIMAL(4,2) NULL,
  nota_parcial3 DECIMAL(4,2) NULL,
  nota_final DECIMAL(4,2) NOT NULL,
  estado ENUM('en_curso','aprobado','reprobado') NOT NULL DEFAULT 'en_curso',
  semestre TINYINT UNSIGNED NOT NULL DEFAULT 1,
  observaciones TEXT NULL,
  num_parciales TINYINT UNSIGNED NOT NULL DEFAULT 2,
  creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_calificacion_inscripcion (inscripcion_id),
  KEY idx_calificacion_estudiante (estudiante_id),
  KEY idx_calificacion_materia (materia_id),
  KEY idx_calificacion_estado (estado),
  CONSTRAINT fk_calificacion_inscripcion
    FOREIGN KEY (inscripcion_id) REFERENCES inscripcion(inscripcion_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT fk_calificacion_estudiante
    FOREIGN KEY (estudiante_id) REFERENCES estudiante(estudiante_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT fk_calificacion_materia
    FOREIGN KEY (materia_id) REFERENCES materia(materia_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  CONSTRAINT chk_calificacion_rango CHECK (
    (nota_parcial1 IS NULL OR (nota_parcial1 >= 0 AND nota_parcial1 <= 10)) AND
    (nota_parcial2 IS NULL OR (nota_parcial2 >= 0 AND nota_parcial2 <= 10)) AND
    (nota_parcial3 IS NULL OR (nota_parcial3 >= 0 AND nota_parcial3 <= 10)) AND
    (nota_final >= 0 AND nota_final <= 10)
  )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE recomendacion (
  recomendacion_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  estudiante_id INT UNSIGNED NOT NULL,
  materia_id INT UNSIGNED NULL,
  nivel_id INT UNSIGNED NULL,
  tipo_recomendacion VARCHAR(50) NOT NULL,
  descripcion TEXT NOT NULL,
  prioridad ENUM('alta','media','baja') NOT NULL DEFAULT 'media',
  estado ENUM('activa','vista','resuelta','archivada') NOT NULL DEFAULT 'activa',
  fuente ENUM('manual','automatica') NOT NULL DEFAULT 'automatica',
  fecha_creacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  fecha_actualizacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_recomendacion_estudiante (estudiante_id),
  KEY idx_recomendacion_estado_prioridad (estado, prioridad),
  KEY idx_recomendacion_tipo (tipo_recomendacion),
  CONSTRAINT fk_recomendacion_estudiante
    FOREIGN KEY (estudiante_id) REFERENCES estudiante(estudiante_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT fk_recomendacion_materia
    FOREIGN KEY (materia_id) REFERENCES materia(materia_id)
    ON UPDATE CASCADE
    ON DELETE SET NULL,
  CONSTRAINT fk_recomendacion_nivel
    FOREIGN KEY (nivel_id) REFERENCES nivel_rendimiento(nivel_id)
    ON UPDATE CASCADE
    ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE seguimiento_recomendacion (
  seguimiento_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  recomendacion_id INT UNSIGNED NOT NULL,
  estudiante_id INT UNSIGNED NOT NULL,
  calificacion_id INT UNSIGNED NULL,
  fecha_generada DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  recomendacion_visualizada BOOLEAN NOT NULL DEFAULT FALSE,
  fecha_visualizacion DATETIME NULL,
  enlace_visitado BOOLEAN NOT NULL DEFAULT FALSE,
  recomendacion_confirmada BOOLEAN NOT NULL DEFAULT FALSE,
  fecha_confirmacion DATETIME NULL,
  observaciones TEXT NULL,
  creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_seguimiento_recomendacion (recomendacion_id),
  KEY idx_seguimiento_estudiante (estudiante_id),
  CONSTRAINT fk_seguimiento_recomendacion
    FOREIGN KEY (recomendacion_id) REFERENCES recomendacion(recomendacion_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT fk_seguimiento_estudiante
    FOREIGN KEY (estudiante_id) REFERENCES estudiante(estudiante_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT fk_seguimiento_calificacion
    FOREIGN KEY (calificacion_id) REFERENCES calificacion(calificacion_id)
    ON UPDATE CASCADE
    ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE interaccion_contenido (
  interaccion_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  seguimiento_id INT UNSIGNED NOT NULL,
  fecha_inicio DATETIME NULL,
  fecha_fin DATETIME NULL,
  tiempo_segundos INT UNSIGNED NULL,
  tipo_interaccion VARCHAR(50) NULL,
  creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_interaccion_seguimiento (seguimiento_id),
  CONSTRAINT fk_interaccion_seguimiento
    FOREIGN KEY (seguimiento_id) REFERENCES seguimiento_recomendacion(seguimiento_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==========================================================
-- EVALUACIONES
-- ==========================================================

CREATE TABLE evaluacion (
  evaluacion_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  recomendacion_id INT UNSIGNED NOT NULL,
  titulo VARCHAR(150) NOT NULL,
  descripcion VARCHAR(255) NULL,
  estado ENUM('activa','inactiva') NOT NULL DEFAULT 'activa',
  creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_evaluacion_recomendacion (recomendacion_id),
  CONSTRAINT fk_evaluacion_recomendacion
    FOREIGN KEY (recomendacion_id) REFERENCES recomendacion(recomendacion_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE pregunta (
  pregunta_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  evaluacion_id INT UNSIGNED NOT NULL,
  texto_pregunta TEXT NOT NULL,
  tipo_pregunta ENUM('abierta','opcion_multiple','si_no','escala') NOT NULL DEFAULT 'abierta',
  orden INT UNSIGNED NOT NULL DEFAULT 1,
  requerida BOOLEAN NOT NULL DEFAULT TRUE,
  creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_pregunta_evaluacion (evaluacion_id),
  CONSTRAINT fk_pregunta_evaluacion
    FOREIGN KEY (evaluacion_id) REFERENCES evaluacion(evaluacion_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE opcion_respuesta (
  opcion_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  pregunta_id INT UNSIGNED NOT NULL,
  texto_opcion VARCHAR(255) NOT NULL,
  es_correcta BOOLEAN NOT NULL DEFAULT FALSE,
  orden INT UNSIGNED NOT NULL DEFAULT 1,
  creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_opcion_pregunta (pregunta_id),
  CONSTRAINT fk_opcion_pregunta
    FOREIGN KEY (pregunta_id) REFERENCES pregunta(pregunta_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE evaluacion_estudiante (
  evaluacion_estudiante_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  seguimiento_id INT UNSIGNED NOT NULL,
  evaluacion_id INT UNSIGNED NOT NULL,
  fecha_inicio DATETIME NULL,
  fecha_fin DATETIME NULL,
  tiempo_limite_segundos INT UNSIGNED NULL,
  evaluacion_aprobada BOOLEAN NOT NULL DEFAULT FALSE,
  estado ENUM('pendiente','en_progreso','finalizada','aprobada','reprobada') NOT NULL DEFAULT 'pendiente',
  creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_evaluacion_estudiante (seguimiento_id, evaluacion_id),
  KEY idx_eval_estudiante_seguimiento (seguimiento_id),
  KEY idx_eval_estudiante_evaluacion (evaluacion_id),
  CONSTRAINT fk_evaluacion_estudiante_seguimiento
    FOREIGN KEY (seguimiento_id) REFERENCES seguimiento_recomendacion(seguimiento_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT fk_evaluacion_estudiante_evaluacion
    FOREIGN KEY (evaluacion_id) REFERENCES evaluacion(evaluacion_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE intento_evaluacion (
  intento_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  evaluacion_estudiante_id INT UNSIGNED NOT NULL,
  numero_intento INT UNSIGNED NOT NULL DEFAULT 1,
  respuestas_correctas INT UNSIGNED NOT NULL DEFAULT 0,
  fecha_intento DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  estado ENUM('enviado','aceptado','rechazado') NOT NULL DEFAULT 'enviado',
  creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_intento_por_evaluacion (evaluacion_estudiante_id, numero_intento),
  KEY idx_intento_evaluacion_estudiante (evaluacion_estudiante_id),
  CONSTRAINT fk_intento_evaluacion_estudiante
    FOREIGN KEY (evaluacion_estudiante_id) REFERENCES evaluacion_estudiante(evaluacion_estudiante_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE respuesta_estudiante (
  respuesta_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  intento_id INT UNSIGNED NOT NULL,
  pregunta_id INT UNSIGNED NOT NULL,
  opcion_id INT UNSIGNED NOT NULL,
  es_correcta BOOLEAN NOT NULL DEFAULT FALSE,
  respuesta_texto TEXT NULL,
  calificacion_estrellas TINYINT UNSIGNED NULL CHECK (calificacion_estrellas BETWEEN 1 AND 5),
  retroalimentacion_maestro TEXT NULL,
  fecha_retroalimentacion DATETIME NULL,
  creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_respuesta_intento (intento_id),
  KEY idx_respuesta_pregunta (pregunta_id),
  CONSTRAINT fk_respuesta_intento
    FOREIGN KEY (intento_id) REFERENCES intento_evaluacion(intento_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT fk_respuesta_pregunta
    FOREIGN KEY (pregunta_id) REFERENCES pregunta(pregunta_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT fk_respuesta_opcion
    FOREIGN KEY (opcion_id) REFERENCES opcion_respuesta(opcion_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==========================================================
-- RESPUESTAS PERSONALES PARA EL MOTOR DE RECOMENDACIONES
-- ==========================================================

CREATE TABLE respuesta_personal (
  respuesta_personal_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  estudiante_id INT UNSIGNED NOT NULL,
  pregunta_clave VARCHAR(80) NOT NULL,
  valor_respuesta VARCHAR(255) NOT NULL,
  fecha_respuesta DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_respuesta_personal (estudiante_id, pregunta_clave),
  KEY idx_respuesta_personal_estudiante (estudiante_id),
  CONSTRAINT fk_respuesta_personal_estudiante
    FOREIGN KEY (estudiante_id) REFERENCES estudiante(estudiante_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==========================================================
-- DATOS INICIALES
-- ==========================================================

INSERT IGNORE INTO rol (rol_id, nombre, descripcion) VALUES
(1, 'administrador', 'Administrador del sistema'),
(2, 'estudiante', 'Usuario estudiante'),
(3, 'docente', 'Usuario docente'),
(4, 'coordinador', 'Usuario coordinador');

INSERT IGNORE INTO nivel_rendimiento (nivel_id, nombre, rango_min, rango_max, descripcion) VALUES
(1, 'bajo', 0.00, 2.49, 'Rendimiento bajo'),
(2, 'medio', 2.50, 3.49, 'Rendimiento medio'),
(3, 'alto', 3.50, 4.49, 'Rendimiento alto'),
(4, 'excelente', 4.50, 5.00, 'Rendimiento excelente');

-- ==========================================================
-- PROCEDIMIENTOS Y TRIGGERS
-- ==========================================================

DROP PROCEDURE IF EXISTS recalcular_estudiante_resumen;

DELIMITER $$

CREATE PROCEDURE recalcular_estudiante_resumen(IN p_estudiante_id INT UNSIGNED)
BEGIN
  DECLARE v_promedio DECIMAL(4,2);
  DECLARE v_estado VARCHAR(20);

  SELECT COALESCE(ROUND(AVG(nota_final), 2), 0.00)
    INTO v_promedio
  FROM calificacion
  WHERE estudiante_id = p_estudiante_id;

  IF v_promedio = 0 THEN
    SET v_estado = 'sin_calificar';
  ELSEIF v_promedio < 3.00 THEN
    SET v_estado = 'riesgo';
  ELSEIF v_promedio < 3.50 THEN
    SET v_estado = 'regular';
  ELSEIF v_promedio < 4.50 THEN
    SET v_estado = 'bueno';
  ELSE
    SET v_estado = 'excelente';
  END IF;

  UPDATE estudiante
  SET promedio_general = v_promedio,
      estado_academico = v_estado
  WHERE estudiante_id = p_estudiante_id;
END$$

CREATE TRIGGER trg_estudiante_bi
BEFORE INSERT ON estudiante
FOR EACH ROW
BEGIN
  DECLARE v_rol_estudiante TINYINT UNSIGNED;
  SELECT rol_id INTO v_rol_estudiante
  FROM rol
  WHERE nombre = 'estudiante'
  LIMIT 1;

  SET NEW.creado_en = COALESCE(NEW.creado_en, CURRENT_TIMESTAMP);
  SET NEW.actualizado_en = CURRENT_TIMESTAMP;

  IF NEW.usuario_id IS NULL THEN
    INSERT INTO usuario (nombre, correo, contrasena, rol_id, estado, creado_en, actualizado_en)
    VALUES (
      NEW.nombre,
      NEW.correo,
      NEW.contrasena,
      v_rol_estudiante,
      'activo',
      NEW.creado_en,
      CURRENT_TIMESTAMP
    );
    SET NEW.usuario_id = LAST_INSERT_ID();
  END IF;
END$$

CREATE TRIGGER trg_estudiante_bu
BEFORE UPDATE ON estudiante
FOR EACH ROW
BEGIN
  SET NEW.actualizado_en = CURRENT_TIMESTAMP;

  IF NEW.usuario_id IS NOT NULL THEN
    UPDATE usuario
    SET nombre = NEW.nombre,
        correo = NEW.correo,
        contrasena = NEW.contrasena,
        actualizado_en = CURRENT_TIMESTAMP
    WHERE usuario_id = NEW.usuario_id;
  END IF;
END$$

CREATE TRIGGER trg_estudiante_ad
AFTER DELETE ON estudiante
FOR EACH ROW
BEGIN
  IF OLD.usuario_id IS NOT NULL THEN
    DELETE FROM usuario WHERE usuario_id = OLD.usuario_id;
  END IF;
END$$

CREATE TRIGGER trg_calificacion_ai
AFTER INSERT ON calificacion
FOR EACH ROW
BEGIN
  CALL recalcular_estudiante_resumen(NEW.estudiante_id);
END$$

CREATE TRIGGER trg_calificacion_au
AFTER UPDATE ON calificacion
FOR EACH ROW
BEGIN
  CALL recalcular_estudiante_resumen(NEW.estudiante_id);
  IF OLD.estudiante_id <> NEW.estudiante_id THEN
    CALL recalcular_estudiante_resumen(OLD.estudiante_id);
  END IF;
END$$

CREATE TRIGGER trg_calificacion_ad
AFTER DELETE ON calificacion
FOR EACH ROW
BEGIN
  CALL recalcular_estudiante_resumen(OLD.estudiante_id);
END$$

DELIMITER ;

ALTER TABLE estudiante
    ADD COLUMN IF NOT EXISTS fecha_nacimiento DATE NULL,
    ADD COLUMN IF NOT EXISTS sexo VARCHAR(20) NULL,
    ADD COLUMN IF NOT EXISTS nacionalidad VARCHAR(60) NULL,
    ADD COLUMN IF NOT EXISTS direccion VARCHAR(200) NULL,
    ADD COLUMN IF NOT EXISTS matricula VARCHAR(30) NULL,
    ADD COLUMN IF NOT EXISTS modalidad VARCHAR(30) NULL,
    ADD COLUMN IF NOT EXISTS edad INT NULL;
 
-- ── 2. Trigger para calcular edad automáticamente ───────────
DROP TRIGGER IF EXISTS calcular_edad_insert;
DROP TRIGGER IF EXISTS calcular_edad_update;
 
DELIMITER $$
 
CREATE TRIGGER calcular_edad_insert
BEFORE INSERT ON estudiante
FOR EACH ROW
BEGIN
    IF NEW.fecha_nacimiento IS NOT NULL THEN
        SET NEW.edad = TIMESTAMPDIFF(YEAR, NEW.fecha_nacimiento, CURDATE());
    END IF;
END$$
 
CREATE TRIGGER calcular_edad_update
BEFORE UPDATE ON estudiante
FOR EACH ROW
BEGIN
    IF NEW.fecha_nacimiento IS NOT NULL THEN
        SET NEW.edad = TIMESTAMPDIFF(YEAR, NEW.fecha_nacimiento, CURDATE());
    END IF;
END$$
 
DELIMITER ;
 
-- ── 3. Tabla maestro: agregar columnas nuevas ───────────────
ALTER TABLE maestro
    ADD COLUMN IF NOT EXISTS fecha_nacimiento DATE NULL,
    ADD COLUMN IF NOT EXISTS sexo VARCHAR(20) NULL,
    ADD COLUMN IF NOT EXISTS nacionalidad VARCHAR(60) NULL,
    ADD COLUMN IF NOT EXISTS direccion VARCHAR(200) NULL;
 
-- ── 4. Tabla materia_maestro: crear si no existe ────────────
CREATE TABLE IF NOT EXISTS materia_maestro (
    maestro_id  INT NOT NULL,
    materia_id  INT NOT NULL,
    PRIMARY KEY (maestro_id, materia_id),
    FOREIGN KEY (maestro_id) REFERENCES maestro(maestro_id) ON DELETE CASCADE,
    FOREIGN KEY (materia_id) REFERENCES materia(materia_id) ON DELETE CASCADE
);
 
SELECT 'Migración completada exitosamente ✅' AS resultado;


-- ==========================================================
-- FIN
-- ==========================================================

-- ---- Insertar datos de prueba ----

-- Insertar roles (1=Admin, 2=Tutor, 3=Maestro, 4=Estudiante)
INSERT INTO rol (rol_id, nombre, descripcion) VALUES 
(1, 'Admin', 'Administrador del Sistema'),
(2, 'Tutor', 'Tutor o Coordinador'),
(3, 'Maestro', 'Maestro o Docente'),
(4, 'Estudiante', 'Estudiante')
ON DUPLICATE KEY UPDATE nombre=VALUES(nombre);

-- Insertar usuario admin
INSERT INTO usuario (nombre, correo, contrasena, rol_id, estado) 
VALUES ('Administrador SIRA', 'admin@sira.com', 'admin123', 1, 'activo')
ON DUPLICATE KEY UPDATE rol_id=VALUES(rol_id);

-- Insertar usuarios tutores
INSERT INTO usuario (nombre, correo, contrasena, rol_id, estado) 
VALUES ('Tutor Principal', 'tutor@sira.com', 'tutor123', 2, 'activo')
ON DUPLICATE KEY UPDATE rol_id=VALUES(rol_id);

-- Insertar maestros en tabla maestro
INSERT INTO maestro (nombre, correo, contrasena, especialidad) 
VALUES 
('Prof. Juan Pérez', 'maestro@sira.com', 'maestro123', 'Programación'),
('Prof. María García', 'maestro2@sira.com', 'maestro123', 'Matemáticas'),
('Prof. Carlos López', 'maestro3@sira.com', 'maestro123', 'Bases de Datos')
ON DUPLICATE KEY UPDATE especialidad=VALUES(especialidad);

-- Insertar carrera de prueba
INSERT INTO carrera (nombre, codigo, descripcion, duracion_anios, estado) 
VALUES 
('Ingeniería en Sistemas', 'INGS001', 'Carrera en Ingeniería de Sistemas', 4, 'activa'),
('Ingeniería en Administración', 'INGA001', 'Carrera en Ingeniería de Administración', 4, 'activa')
ON DUPLICATE KEY UPDATE estado=VALUES(estado);

-- Insertar plan de estudio
INSERT INTO plan_estudio (carrera_id, nombre, version, vigente) 
SELECT carrera_id, 'Plan 2024', '1.0', TRUE 
FROM carrera WHERE nombre = 'Ingeniería en Sistemas'
ON DUPLICATE KEY UPDATE vigente=VALUES(vigente);

-- Insertar materias
INSERT INTO materia (carrera_id, plan_estudio_id, codigo, nombre, creditos, semestre, estado) 
SELECT c.carrera_id, ps.plan_estudio_id, 'PROG101', 'Programación I', 3, 1, 'activa'
FROM carrera c LEFT JOIN plan_estudio ps ON c.carrera_id = ps.carrera_id
WHERE c.nombre = 'Ingeniería en Sistemas'
ON DUPLICATE KEY UPDATE estado=VALUES(estado);

INSERT INTO materia (carrera_id, plan_estudio_id, codigo, nombre, creditos, semestre, estado) 
SELECT c.carrera_id, ps.plan_estudio_id, 'MATH101', 'Cálculo I', 4, 1, 'activa'
FROM carrera c LEFT JOIN plan_estudio ps ON c.carrera_id = ps.carrera_id
WHERE c.nombre = 'Ingeniería en Sistemas'
ON DUPLICATE KEY UPDATE estado=VALUES(estado);

-- Insertar estudiante de prueba
INSERT INTO estudiante (nombre, correo, contrasena, carrera_id, codigo_estudiante, promedio_general, estado_academico) 
SELECT 'Juan Estudiante', 'estudiante@sira.com', 'estudiante123', carrera_id, '2024001', 3.5, 'bueno'
FROM carrera WHERE nombre = 'Ingeniería en Sistemas'
ON DUPLICATE KEY UPDATE promedio_general=VALUES(promedio_general);

-- Insertar nivel de rendimiento
INSERT INTO nivel_rendimiento (nombre, rango_min, rango_max, descripcion)
VALUES 
('Deficiente', 0.0, 2.0, 'Rendimiento deficiente'),
('Insuficiente', 2.0, 3.0, 'Rendimiento insuficiente'),
('Regular', 3.0, 3.5, 'Rendimiento regular'),
('Bueno', 3.5, 4.2, 'Rendimiento bueno'),
('Excelente', 4.2, 5.0, 'Rendimiento excelente')
ON DUPLICATE KEY UPDATE descripcion=VALUES(descripcion);

-- ==========================================================
-- NUEVOS CAMPOS PARA PROCESO 5: INFORMACIÓN DEMOGRÁFICA
-- ==========================================================

-- Agregar campos demográficos a tabla estudiante
ALTER TABLE estudiante ADD COLUMN IF NOT EXISTS sexo VARCHAR(20) NULL AFTER edad;
ALTER TABLE estudiante ADD COLUMN IF NOT EXISTS nacionalidad VARCHAR(60) NULL AFTER sexo;
ALTER TABLE estudiante ADD COLUMN IF NOT EXISTS direccion TEXT NULL AFTER nacionalidad;
ALTER TABLE estudiante ADD COLUMN IF NOT EXISTS matricula VARCHAR(30) NULL UNIQUE AFTER direccion;
ALTER TABLE estudiante ADD COLUMN IF NOT EXISTS modalidad VARCHAR(30) NULL AFTER matricula;

-- Agregar campos demográficos a tabla maestro
ALTER TABLE maestro ADD COLUMN IF NOT EXISTS sexo VARCHAR(20) NULL AFTER especialidad;
ALTER TABLE maestro ADD COLUMN IF NOT EXISTS nacionalidad VARCHAR(60) NULL AFTER sexo;
ALTER TABLE maestro ADD COLUMN IF NOT EXISTS direccion TEXT NULL AFTER nacionalidad;
ALTER TABLE maestro ADD COLUMN IF NOT EXISTS fecha_nacimiento DATE NULL AFTER direccion;
ALTER TABLE maestro ADD COLUMN IF NOT EXISTS edad TINYINT UNSIGNED NULL AFTER fecha_nacimiento;

-- Para guardar las estrellas y el comentario final en la recomendación
ALTER TABLE recomendacion 
ADD COLUMN IF NOT EXISTS estrellas_docente INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS retroalimentacion_docente TEXT;

-- Para guardar el comentario individual del maestro en cada respuesta del alumno
ALTER TABLE respuesta_estudiante 
ADD COLUMN IF NOT EXISTS retroalimentacion_maestro TEXT;