import 'package:http/http.dart' as http;
import 'dart:convert';
import '../models/carrera.dart';
import '../models/materia.dart';
import '../models/estudiante.dart';
import '../models/calificacion.dart';
import '../models/recomendacion.dart';
import '../models/maestro.dart';
import '../config/app_config.dart';

class ApiService {
 static String get baseUrl => AppConfig.baseUrl;
  static Duration get _timeout => Duration(seconds: AppConfig.timeoutSeconds);

  static Map<String, String> get _json => {'Content-Type': 'application/json'};

  // ── HELPERS ────────────────────────────────────────────────────────────────
  static Future<dynamic> _get(String path) async {
    final r = await http.get(Uri.parse('$baseUrl$path')).timeout(_timeout);
    if (r.statusCode == 200) return jsonDecode(r.body);
    throw Exception('GET $path → ${r.statusCode}: ${r.body}');
  }

  static Future<dynamic> _post(String path, Map<String, dynamic> body) async {
    final r = await http
        .post(Uri.parse('$baseUrl$path'), headers: _json, body: jsonEncode(body))
        .timeout(_timeout);
    if (r.statusCode == 200 || r.statusCode == 201) return jsonDecode(r.body);
    throw Exception('POST $path → ${r.statusCode}: ${r.body}');
  }

  static Future<dynamic> _put(String path, Map<String, dynamic> body) async {
    final r = await http
        .put(Uri.parse('$baseUrl$path'), headers: _json, body: jsonEncode(body))
        .timeout(_timeout);
    if (r.statusCode == 200) return jsonDecode(r.body);
    throw Exception('PUT $path → ${r.statusCode}: ${r.body}');
  }

  static Future<void> _delete(String path) async {
    final r = await http.delete(Uri.parse('$baseUrl$path')).timeout(_timeout);
    if (r.statusCode != 200 && r.statusCode != 204) {
      throw Exception('DELETE $path → ${r.statusCode}: ${r.body}');
    }
  }

  // ==================== AUTHENTICATION ====================
  // Se unificaron las rutas bajo el prefijo /auth según las pruebas de backend[cite: 1]

  static Future<Map<String, dynamic>> loginEstudiante(
      String correo, String contrasena) async {
    return await _post('/auth/estudiantes/login', 
        {'correo': correo.trim(), 'contrasena': contrasena.trim()}) as Map<String, dynamic>;
  }

  static Future<Map<String, dynamic>> loginMaestro(
      String correo, String contrasena) async {
    return await _post('/auth/maestros/login', 
        {'correo': correo.trim(), 'contrasena': contrasena.trim()}) as Map<String, dynamic>;
  }

  static Future<Map<String, dynamic>> loginTutor(
      String correo, String contrasena) async {
    return await _post('/auth/tutores/login', 
        {'correo': correo.trim(), 'contrasena': contrasena.trim()}) as Map<String, dynamic>;
  }

  static Future<Map<String, dynamic>> loginAdmin(
      String correo, String contrasena) async {
    return await _post('/auth/admin/login', 
        {'correo': correo.trim(), 'contrasena': contrasena.trim()}) as Map<String, dynamic>;
  }

  // ==================== CARRERAS ====================
  static Future<List<Carrera>> getCarreras() async {
    final data = await _get('/carreras') as List<dynamic>;
    return data.map((c) => Carrera.fromJson(c as Map<String, dynamic>)).toList();
  }

  static Future<Carrera> createCarrera(Carrera c) async {
    final data = await _post('/carreras', c.toJson()) as Map<String, dynamic>;
    return Carrera.fromJson(data);
  }

  static Future<void> updateCarrera(int id, Carrera c) async =>
      await _put('/carreras/$id', c.toJson());

  static Future<void> deleteCarrera(int id) async =>
      await _delete('/carreras/$id');

  // ==================== MATERIAS ====================
  static Future<List<Materia>> getMaterias() async {
    final data = await _get('/materias') as List<dynamic>;
    return data.map((m) => Materia.fromJson(m as Map<String, dynamic>)).toList();
  }

  static Future<List<Materia>> getMateriasByCarrera(int carreraId) async {
    final data = await _get('/materias?carrera_id=$carreraId') as List<dynamic>;
    return data.map((m) => Materia.fromJson(m as Map<String, dynamic>)).toList();
  }

  static Future<Materia> createMateria(Materia m) async {
    final data = await _post('/materias', m.toJson()) as Map<String, dynamic>;
    return Materia.fromJson(data);
  }

  static Future<void> updateMateria(int id, Materia m) async =>
      await _put('/materias/$id', m.toJson());

  static Future<void> deleteMateria(int id) async =>
      await _delete('/materias/$id');

  // ==================== ESTUDIANTES ====================
  static Future<List<Estudiante>> getEstudiantes() async {
    final data = await _get('/estudiantes') as List<dynamic>;
    return data.map((e) => Estudiante.fromJson(e as Map<String, dynamic>)).toList();
  }

  static Future<Estudiante> getEstudianteById(int id) async {
    final data = await _get('/estudiantes/$id') as Map<String, dynamic>;
    return Estudiante.fromJson(data);
  }

  static Future<Estudiante> createEstudiante(Estudiante e) async {
    final data = await _post('/estudiantes', e.toJson()) as Map<String, dynamic>;
    return Estudiante.fromJson(data);
  }

  static Future<void> updateEstudiante(int id, Estudiante e) async =>
      await _put('/estudiantes/$id', e.toJson());

  static Future<void> deleteEstudiante(int id) async =>
      await _delete('/estudiantes/$id');

  // ==================== MAESTROS ====================
  static Future<List<Maestro>> getMaestros() async {
    final data = await _get('/maestros') as List<dynamic>;
    return data.map((m) => Maestro.fromJson(m as Map<String, dynamic>)).toList();
  }

  static Future<Maestro> createMaestro(Maestro m) async {
    final data = await _post('/maestros', m.toJson()) as Map<String, dynamic>;
    return Maestro.fromJson(data);
  }

  static Future<void> updateMaestro(int id, Maestro m) async =>
      await _put('/maestros/$id', m.toJson());

  static Future<void> deleteMaestro(int id) async =>
      await _delete('/maestros/$id');

  static Future<List<Materia>> getMateriasDelMaestro(int maestroId) async {
    final data = await _get('/maestros/$maestroId/materias') as List<dynamic>;
    return data.map((m) => Materia.fromJson(m as Map<String, dynamic>)).toList();
  }

  static Future<List<Map<String, dynamic>>> getEstudiantesDeMateriaMaestro(
      int maestroId, int materiaId) async {
    final data = await _get(
        '/maestros/$maestroId/materias/$materiaId/estudiantes') as List<dynamic>;
    return data.cast<Map<String, dynamic>>();
  }

  static Future<void> asignarMateriaMaestro(
          int maestroId, int materiaId) async =>
      await _post('/maestros/$maestroId/materias/$materiaId', {});

  static Future<void> quitarMateriaMaestro(
          int maestroId, int materiaId) async =>
      await _delete('/maestros/$maestroId/materias/$materiaId');

  // ==================== CALIFICACIONES ====================
  static Future<List<Calificacion>> getCalificaciones(
      {int? estudianteId, int? materiaId}) async {
    String path = '/calificaciones';
    final params = <String>[];
    if (estudianteId != null) params.add('estudiante_id=$estudianteId');
    if (materiaId != null) params.add('materia_id=$materiaId');
    if (params.isNotEmpty) path += '?${params.join('&')}';
    final data = await _get(path) as List<dynamic>;
    return data
        .map((c) => Calificacion.fromJson(c as Map<String, dynamic>))
        .toList();
  }

  static Future<List<Calificacion>> getCalificacionesByEstudiante(
      int estudianteId) async {
    final data =
        await _get('/calificaciones/estudiante/$estudianteId') as List<dynamic>;
    return data
        .map((c) => Calificacion.fromJson(c as Map<String, dynamic>))
        .toList();
  }

  static Future<Calificacion> createCalificacion(Calificacion c) async {
    final body = {
      'estudiante_id': c.estudianteId,
      'materia_id': c.materiaId,
      if (c.notaParcial1 != null) 'parcial1': c.notaParcial1,
      if (c.notaParcial2 != null) 'parcial2': c.notaParcial2,
      if (c.notaFinal != null) 'nota_final': c.notaFinal,
      'estado': c.estado,
      'semestre': c.semestre ?? 1,
    };
    final data = await _post('/calificaciones', body) as Map<String, dynamic>;
    return Calificacion.fromJson(data);
  }

  static Future<void> updateCalificacion(int id, Calificacion c) async {
    final body = <String, dynamic>{
      if (c.notaParcial1 != null) 'parcial1': c.notaParcial1,
      if (c.notaParcial2 != null) 'parcial2': c.notaParcial2,
      if (c.notaFinal != null) 'nota_final': c.notaFinal,
      'estado': c.estado,
      if (c.semestre != null) 'semestre': c.semestre,
    };
    await _put('/calificaciones/$id', body);
  }

  static Future<void> deleteCalificacion(int id) async =>
      await _delete('/calificaciones/$id');

  // ==================== RECOMENDACIONES ====================
  static Future<List<Recomendacion>> getRecomendaciones(
      {int? estudianteId, String? prioridad, String? estado}) async {
    String path = '/recomendaciones';
    final params = <String>[];
    if (estudianteId != null) params.add('estudiante_id=$estudianteId');
    if (prioridad != null) params.add('prioridad=$prioridad');
    if (estado != null) params.add('estado=$estado');
    if (params.isNotEmpty) path += '?${params.join('&')}';
    final data = await _get(path) as List<dynamic>;
    return data
        .map((r) => Recomendacion.fromJson(r as Map<String, dynamic>))
        .toList();
  }

  static Future<List<Recomendacion>> getRecomendacionesByEstudiante(
      int estudianteId) async =>
      getRecomendaciones(estudianteId: estudianteId);

  static Future<Recomendacion> createRecomendacion(Recomendacion r) async {
    final data =
        await _post('/recomendaciones', r.toJson()) as Map<String, dynamic>;
    return Recomendacion.fromJson(data);
  }

  static Future<void> updateRecomendacion(int id, Recomendacion r) async =>
      await _put('/recomendaciones/$id', r.toJson());

  static Future<void> deleteRecomendacion(int id) async =>
      await _delete('/recomendaciones/$id');

  static Future<Map<String, dynamic>> generarRecomendacionPorCalificacion(int calificacionId) async =>
      await _post('/recomendaciones/generar/por-calificacion/$calificacionId', {}) as Map<String, dynamic>;

  // ==================== INSCRIPCIONES ====================
  static Future<List<Map<String, dynamic>>> getInscripciones() async {
    final data = await _get('/inscripciones') as List<dynamic>;
    return data.cast<Map<String, dynamic>>();
  }

  static Future<List<Map<String, dynamic>>> getInscripcionesByEstudiante(int estudianteId) async {
    final data = await _get('/inscripciones/estudiante/$estudianteId') as List<dynamic>;
    return data.cast<Map<String, dynamic>>();
  }

  static Future<List<Map<String, dynamic>>> getInscripcionesByMateria(int materiaId) async {
    final data = await _get('/inscripciones/materia/$materiaId') as List<dynamic>;
    return data.cast<Map<String, dynamic>>();
  }

  static Future<Map<String, dynamic>> createInscripcion(Map<String, dynamic> data) async =>
      await _post('/inscripciones', data) as Map<String, dynamic>;

  static Future<void> updateInscripcion(int id, Map<String, dynamic> data) async =>
      await _put('/inscripciones/$id', data);

  static Future<void> deleteInscripcion(int id) async =>
      await _delete('/inscripciones/$id');

  // ==================== EVALUACIONES ====================
  static Future<List<Map<String, dynamic>>> getEvaluaciones({
    int? recomendacionId,
    String? estado,
  }) async {
    String path = '/evaluaciones';
    final params = <String>[];
    if (recomendacionId != null) params.add('recomendacion_id=$recomendacionId');
    if (estado != null) params.add('estado=$estado');
    if (params.isNotEmpty) path += '?${params.join('&')}';
    final data = await _get(path) as List<dynamic>;
    return data.cast<Map<String, dynamic>>();
  }

  static Future<Map<String, dynamic>> createEvaluacion(Map<String, dynamic> data) async =>
      await _post('/evaluaciones', data) as Map<String, dynamic>;

  static Future<void> updateEvaluacion(int id, Map<String, dynamic> data) async =>
      await _put('/evaluaciones/$id', data);

  static Future<void> deleteEvaluacion(int id) async =>
      await _delete('/evaluaciones/$id');

  static Future<List<Map<String, dynamic>>> getPreguntasByEvaluacion(int evaluacionId) async {
    final data = await _get('/evaluaciones/preguntas/evaluacion/$evaluacionId') as List<dynamic>;
    return data.cast<Map<String, dynamic>>();
  }

  static Future<Map<String, dynamic>> createPregunta(Map<String, dynamic> data) async =>
      await _post('/evaluaciones/preguntas', data) as Map<String, dynamic>;

  static Future<void> updatePregunta(int id, Map<String, dynamic> data) async =>
      await _put('/evaluaciones/preguntas/$id', data);

  static Future<void> deletePregunta(int id) async =>
      await _delete('/evaluaciones/preguntas/$id');

  static Future<List<Map<String, dynamic>>> getOpcionesByPregunta(int preguntaId) async {
    final data = await _get('/evaluaciones/opciones/pregunta/$preguntaId') as List<dynamic>;
    return data.cast<Map<String, dynamic>>();
  }

  static Future<Map<String, dynamic>> createOpcion(Map<String, dynamic> data) async =>
      await _post('/evaluaciones/opciones', data) as Map<String, dynamic>;

  static Future<void> updateOpcion(int id, Map<String, dynamic> data) async =>
      await _put('/evaluaciones/opciones/$id', data);

  static Future<void> deleteOpcion(int id) async =>
      await _delete('/evaluaciones/opciones/$id');

  // ==================== HEALTH ====================
  static Future<bool> checkConnection() async {
    try {
      final r = await http
          .get(Uri.parse(baseUrl.replaceAll('/api', '/')))
          .timeout(const Duration(seconds: 5));
      return r.statusCode == 200;
    } catch (_) {
      return false;
    }
  }
}