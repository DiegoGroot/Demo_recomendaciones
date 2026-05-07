-- ================================================================
-- SIRA — Fix constraints de escala (ejecutar con: sudo mysql sira < fix_constraints.sql)
-- ================================================================
USE sira;

-- 1. Fix promedio_general del estudiante: de 0-5 a 0-10
ALTER TABLE estudiante DROP CONSTRAINT chk_estudiante_promedio;
ALTER TABLE estudiante ADD CONSTRAINT chk_estudiante_promedio
    CHECK (promedio_general BETWEEN 0 AND 10);

-- 2. Fix notas de calificación: de 0-5 a 0-10 (por si no se aplicó antes)
ALTER TABLE calificacion DROP CONSTRAINT IF EXISTS chk_calificacion_rango;
ALTER TABLE calificacion ADD CONSTRAINT chk_calificacion_rango CHECK (
    (nota_parcial1 IS NULL OR nota_parcial1 BETWEEN 0 AND 10) AND
    (nota_parcial2 IS NULL OR nota_parcial2 BETWEEN 0 AND 10) AND
    (nota_parcial3 IS NULL OR nota_parcial3 BETWEEN 0 AND 10) AND
    (nota_final BETWEEN 0 AND 10)
);

SELECT 'Constraints actualizados a escala 0-10 ✅' AS resultado;