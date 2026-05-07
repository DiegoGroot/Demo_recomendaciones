import 'package:http/http.dart' as http;
import 'dart:convert';
import '../models/carrera.dart';
import '../models/materia.dart';
import '../models/recomendacion.dart';
import '../models/estudiante.dart';
import '../models/calificacion.dart';
import '../config/app_config.dart';

class ApiService {
  static String get baseUrl => AppConfig.baseUrl;

  static Future<dynamic> _get(String path) async {
    final r = await http.get(Uri.parse('$baseUrl$path'));
    if (r.statusCode == 200) return jsonDecode(r.body);
    throw Exception('Error GET: ${r.statusCode}');
  }

  static Future<dynamic> _post(String path, dynamic data) async {
    final r = await http.post(
      Uri.parse('$baseUrl$path'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(data),
    );
    if (r.statusCode == 200 || r.statusCode == 201) return jsonDecode(r.body);
    throw Exception('Error POST: ${r.statusCode} - ${r.body}');
  }

  static Future<dynamic> _put(String path, dynamic data) async {
    final r = await http.put(
      Uri.parse('$baseUrl$path'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(data),
    );
    if (r.statusCode == 200) return jsonDecode(r.body);
    throw Exception('Error PUT: ${r.statusCode}');
  }

  static Future<void> _delete(String path) async {
    final r = await http.delete(Uri.parse('$baseUrl$path'));
    if (r.statusCode != 200 && r.statusCode != 204) {
      throw Exception('Error DELETE: ${r.statusCode}');
    }
  }

  // ============ MATERIAS ============
  static Future<List<Materia>> getMaterias() async {
    final data = await _get('/materias');
    return (data as List).map((i) => Materia.fromJson(i)).toList();
  }

  static Future<Materia> createMateria(Materia materia) async {
    final data = await _post('/materias', materia.toJson());
    return Materia.fromJson(data);
  }

  static Future<Materia> updateMateria(int id, Materia materia) async {
    final data = await _put('/materias/$id', materia.toJson());
    return Materia.fromJson(data);
  }

  static Future<void> deleteMateria(int id) async {
    await _delete('/materias/$id');
  }

  // ============ CARRERAS ============
  static Future<List<Carrera>> getCarreras() async {
    final data = await _get('/carreras');
    return (data as List).map((i) => Carrera.fromJson(i)).toList();
  }

  static Future<Carrera> createCarrera(Carrera carrera) async {
    final data = await _post('/carreras', carrera.toJson());
    return Carrera.fromJson(data);
  }

  static Future<Carrera> updateCarrera(int id, Carrera carrera) async {
    final data = await _put('/carreras/$id', carrera.toJson());
    return Carrera.fromJson(data);
  }

  static Future<void> deleteCarrera(int id) async {
    await _delete('/carreras/$id');
  }

  // ============ ESTUDIANTES ============
  static Future<List<Estudiante>> getEstudiantes() async {
    final data = await _get('/estudiantes');
    return (data as List).map((i) => Estudiante.fromJson(i)).toList();
  }

  static Future<Estudiante> createEstudiante(Estudiante estudiante) async {
    final data = await _post('/estudiantes', estudiante.toJson());
    return Estudiante.fromJson(data);
  }

  static Future<Estudiante> updateEstudiante(int id, Estudiante estudiante) async {
    final data = await _put('/estudiantes/$id', estudiante.toJson());
    return Estudiante.fromJson(data);
  }

  static Future<void> deleteEstudiante(int id) async {
    await _delete('/estudiantes/$id');
  }

  static Future<Map<String, dynamic>> registrarEstudiante(Estudiante estudiante) async {
    final data = await _post('/estudiantes/registro', estudiante.toJson());
    return data;
  }

  // ============ RECOMENDACIONES ============
  static Future<List<Recomendacion>> getRecomendaciones() async {
    final data = await _get('/recomendaciones');
    return (data as List).map((i) => Recomendacion.fromJson(i)).toList();
  }

  static Future<List<Recomendacion>> getRecomendacionesByEstudiante(int estId) async {
    final data = await _get('/estudiantes/$estId/recomendaciones');
    return (data as List).map((i) => Recomendacion.fromJson(i)).toList();
  }

  static Future<Recomendacion> createRecomendacion(Recomendacion recomendacion) async {
    final data = await _post('/recomendaciones', recomendacion.toJson());
    return Recomendacion.fromJson(data);
  }

  static Future<Recomendacion> updateRecomendacion(int id, Recomendacion recomendacion) async {
    final data = await _put('/recomendaciones/$id', recomendacion.toJson());
    return Recomendacion.fromJson(data);
  }

  static Future<void> deleteRecomendacion(int id) async {
    await _delete('/recomendaciones/$id');
  }

  static Future<Map<String, dynamic>> calificarRecomendacion(int id, int calificacion) async {
    final data = await _post('/recomendaciones/$id/calificar', {'calificacion': calificacion});
    return data;
  }

  // ============ CALIFICACIONES ============
  static Future<List<Calificacion>> getCalificaciones() async {
    final data = await _get('/calificaciones');
    return (data as List).map((i) => Calificacion.fromJson(i)).toList();
  }

  static Future<List<Calificacion>> getCalificacionesByEstudiante(int estId) async {
    final data = await _get('/estudiantes/$estId/calificaciones');
    return (data as List).map((i) => Calificacion.fromJson(i)).toList();
  }

  static Future<Calificacion> createCalificacion(Calificacion calificacion) async {
    final data = await _post('/calificaciones', calificacion.toJson());
    return Calificacion.fromJson(data);
  }

  static Future<Calificacion> updateCalificacion(int id, Calificacion calificacion) async {
    final data = await _put('/calificaciones/$id', calificacion.toJson());
    return Calificacion.fromJson(data);
  }

  // ============ EVALUACIONES ============
  static Future<List<dynamic>> getEvaluacionesByEstudiante(int estId) async {
    final data = await _get('/estudiantes/$estId/evaluaciones');
    return (data as List).toList();
  }

  static Future<List<dynamic>> getPreguntas(int evalId) async {
    final data = await _get('/evaluaciones/$evalId/preguntas');
    return (data as List).toList();
  }

  static Future<Map<String, dynamic>> createEvaluacion(Map<String, dynamic> data) async {
    return await _post('/evaluaciones', data);
  }

  static Future<Map<String, dynamic>> createPregunta(Map<String, dynamic> data) async {
    return await _post('/evaluaciones/preguntas', data);
  }

  static Future<Map<String, dynamic>> createOpcion(Map<String, dynamic> data) async {
    return await _post('/evaluaciones/opciones', data);
  }

  static Future<Map<String, dynamic>> submitRespuestasEstudiante(Map<String, dynamic> data) async {
    return await _post('/evaluaciones/respuestas', data);
  }

  static Future<Map<String, dynamic>> getResultadosEstudiante(int estId) async {
    return await _get('/estudiantes/$estId/resultados');
  }

  // ============ AUTH ============
  static Future<Map<String, dynamic>> loginAdmin(String correo, String contrasena) async {
    return await _post('/auth/admin/login', {'correo': correo, 'contrasena': contrasena}) as Map<String, dynamic>;
  }

  static Future<Map<String, dynamic>> loginEstudiante(String correo, String contrasena) async {
    return await _post('/auth/estudiantes/login', {'correo': correo, 'contrasena': contrasena}) as Map<String, dynamic>;
  }

  static Future<Map<String, dynamic>> loginMaestro(String correo, String contrasena) async {
    return await _post('/auth/maestros/login', {'correo': correo, 'contrasena': contrasena}) as Map<String, dynamic>;
  }

  static Future<Map<String, dynamic>> loginTutor(String correo, String contrasena) async {
    return await _post('/auth/tutores/login', {'correo': correo, 'contrasena': contrasena}) as Map<String, dynamic>;
  }
}
