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

SELECT 'Migración completada ✅' AS resultado;