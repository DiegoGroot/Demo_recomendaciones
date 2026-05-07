-- Verificar si la BD y datos existen
USE sira;
SELECT COUNT(*) as usuarios FROM usuario;
SELECT COUNT(*) as estudiantes FROM estudiante;
SELECT COUNT(*) as materias FROM materia;
SELECT * FROM usuario WHERE correo = 'admin@sira.com';
