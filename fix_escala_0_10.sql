-- ================================================================
-- SIRA — Fix: cambiar escala de calificaciones de 0-5 a 0-10
-- Ejecutar en tu BD MySQL una sola vez
-- ================================================================

USE sira;

-- 1. Eliminar el constraint actual (escala 0-5)
ALTER TABLE calificacion
    DROP CONSTRAINT chk_calificacion_rango;

-- 2. Agregar el constraint correcto (escala 0-10)
ALTER TABLE calificacion
    ADD CONSTRAINT chk_calificacion_rango CHECK (
        (nota_parcial1 IS NULL OR nota_parcial1 BETWEEN 0 AND 10) AND
        (nota_parcial2 IS NULL OR nota_parcial2 BETWEEN 0 AND 10) AND
        (nota_parcial3 IS NULL OR nota_parcial3 BETWEEN 0 AND 10) AND
        (nota_final BETWEEN 0 AND 10)
    );

-- 3. Verificar que el cambio se aplicó correctamente
SELECT
    CONSTRAINT_NAME,
    CHECK_CLAUSE
FROM INFORMATION_SCHEMA.CHECK_CONSTRAINTS
WHERE CONSTRAINT_SCHEMA = 'sira'
  AND CONSTRAINT_NAME = 'chk_calificacion_rango';

SELECT 'Escala actualizada a 0-10 ✅' AS resultado;