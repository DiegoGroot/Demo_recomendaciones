import 'package:http/http.dart' as http;
import 'dart:convert';
import '../models/carrera.dart';
import '../models/materia.dart';
import '../models/estudiante.dart';
import '../models/calificacion.dart';
import '../models/recomendacion.dart';
import '../config/app_config.dart';

class ApiService {
  static String get baseUrl => AppConfig.baseUrl;
  static Duration get _timeout => Duration(seconds: AppConfig.timeoutSeconds);
  static Map<String, String> get _json => {'Content-Type': 'application/json'};

  // ── HELPERS ───────────────────────────────────────────────────────────────
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

  // ==================== AUTH ====================
  static Future<Map<String, dynamic>> loginEstudiante(
      String correo, String contrasena) async =>
      await _post('/auth/estudiantes/login',
          {'correo': correo.trim(), 'contrasena': contrasena.trim()}) as Map<String, dynamic>;

  static Future<Map<String, dynamic>> loginMaestro(
      String correo, String contrasena) async =>
      await _post('/auth/maestros/login',
          {'correo': correo.trim(), 'contrasena': contrasena.trim()}) as Map<String, dynamic>;

  static Future<Map<String, dynamic>> loginTutor(
      String correo, String contrasena) async =>
      await _post('/auth/tutores/login',
          {'correo': correo.trim(), 'contrasena': contrasena.trim()}) as Map<String, dynamic>;

  static Future<Map<String, dynamic>> loginAdmin(
      String correo, String contrasena) async =>
      await _post('/auth/admin/login',
          {'correo': correo.trim(), 'contrasena': contrasena.trim()}) as Map<String, dynamic>;

  static Future<Map<String, dynamic>> registrarEstudiante({
    required String nombre,
    required String correo,
    required String contrasena,
    int? carreraId,
    String? matricula,
  }) async =>
      await _post('/estudiantes/registro', {
        'nombre': nombre,
        'correo': correo,
        'contrasena': contrasena,
        if (carreraId != null) 'carrera_id': carreraId,
        if (matricula != null) 'matricula': matricula,
      }) as Map<String, dynamic>;

  // ==================== CARRERAS ====================
  static Future<List<Carrera>> getCarreras() async {
    final data = await _get('/carreras') as List<dynamic>;
    return data.map((c) => Carrera.fromJson(c as Map<String, dynamic>)).toList();
  }

  static Future<void> createCarrera(Carrera carrera) async =>
      await _post('/carreras', carrera.toJson());

  static Future<void> updateCarrera(int id, Carrera carrera) async =>
      await _put('/carreras/$id', carrera.toJson());

  static Future<void> deleteCarrera(int id) async =>
      await _delete('/carreras/$id');

   static Future<Map<String, dynamic>> importarMapaCurricular(int carreraId, String urlPdf) async =>
      await _post('/carreras/$carreraId/importar-mapa', {'url_pdf': urlPdf}) as Map<String, dynamic>;   

  // ==================== MATERIAS ====================
  static Future<List<Materia>> getMaterias() async {
    final data = await _get('/materias') as List<dynamic>;
    return data.map((m) {
      final map = m as Map<String, dynamic>;
      return Materia(
        materiaId: map['materia_id'] ?? map['id'] ?? 0,
        nombre: map['nombre'] ?? 'Sin nombre',
        codigo: map['codigo'] ?? '',
        carreraId: map['carrera_id'] ?? 0,
      );
    }).toList();
  }

  static Future<List<Materia>> getMateriasByCarrera(int carreraId) async {
    final data = await _get('/materias?carrera_id=$carreraId') as List<dynamic>;
    return data.map((m) => Materia.fromJson(m as Map<String, dynamic>)).toList();
  }

  // ── NUEVO: Extraer materias crudas para poder leer el "semestre" ────────
  static Future<List<Map<String, dynamic>>> getMateriasRawByCarrera(int carreraId) async {
    final data = await _get('/materias') as List<dynamic>;
    final allMaterias = data.cast<Map<String, dynamic>>();
    // Filtramos localmente y conservamos todos los datos (como semestre y creditos)
    return allMaterias.where((m) => m['carrera_id'] == carreraId).toList();
  }

  static Future<void> createMateria(Materia materia) async =>
      await _post('/materias', materia.toJson());

  static Future<void> updateMateria(int id, Materia materia) async =>
      await _put('/materias/$id', materia.toJson());

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

  static Future<void> createEstudiante(Estudiante e) async =>
      await _post('/estudiantes', e.toJson());

  static Future<void> updateEstudiante(int id, Estudiante e) async =>
      await _put('/estudiantes/$id', e.toJson());

  static Future<void> deleteEstudiante(int id) async =>
      await _delete('/estudiantes/$id');

  // ==================== CALIFICACIONES ====================
  static Future<List<Calificacion>> getCalificaciones() async {
    final data = await _get('/calificaciones') as List<dynamic>;
    return data.map((c) => Calificacion.fromJson(c as Map<String, dynamic>)).toList();
  }

  static Future<List<Calificacion>> getCalificacionesByEstudiante(int estudianteId) async {
    final data = await _get('/calificaciones/estudiante/$estudianteId') as List<dynamic>;
    return data.map((c) => Calificacion.fromJson(c as Map<String, dynamic>)).toList();
  }

  static Future<void> createCalificacion(Map<String, dynamic> data) async =>
      await _post('/calificaciones', data);

  static Future<void> updateCalificacion(int id, Map<String, dynamic> data) async =>
      await _put('/calificaciones/$id', data);

  static Future<void> deleteCalificacion(int id) async =>
      await _delete('/calificaciones/$id');

  static Future<Map<String, dynamic>> generarRecomendacion(int calificacionId) async =>
      await _post('/recomendaciones/generar/por-calificacion/$calificacionId', {})
          as Map<String, dynamic>;

  // ==================== RECOMENDACIONES ====================
  static Future<List<Recomendacion>> getRecomendaciones() async {
    final data = await _get('/recomendaciones') as List<dynamic>;
    return data.map((r) => Recomendacion.fromJson(r as Map<String, dynamic>)).toList();
  }

  static Future<List<Recomendacion>> getRecomendacionesByEstudiante(int estudianteId) async {
    try {
      final data = await _get('/recomendaciones?estudiante_id=$estudianteId') as List<dynamic>;
      return data.map((r) => Recomendacion.fromJson(r as Map<String, dynamic>)).toList();
    } catch (_) {
      return [];
    }
  }

  static Future<void> calificarRecomendacion(int recomendacionId, int calificacion) async =>
      await _post('/recomendaciones/$recomendacionId/calificar', {'calificacion': calificacion});

  static Future<void> createRecomendacion(Recomendacion r) async =>
      await _post('/recomendaciones', r.toJson());

  static Future<void> updateRecomendacion(int id, Recomendacion r) async =>
      await _put('/recomendaciones/$id', r.toJson());

  static Future<void> deleteRecomendacion(int id) async =>
      await _delete('/recomendaciones/$id');

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

  static Future<List<Map<String, dynamic>>> getEvaluacionesByEstudiante(int estudianteId) async {
    try {
      final data = await _get('/evaluaciones/estudiante/$estudianteId') as List<dynamic>;
      return List<Map<String, dynamic>>.from(data);
    } catch (_) {
      return [];
    }
  }

  static Future<Map<String, dynamic>> createEvaluacion(Map<String, dynamic> data) async =>
      await _post('/evaluaciones', data) as Map<String, dynamic>;

  static Future<void> updateEvaluacion(int id, Map<String, dynamic> data) async =>
      await _put('/evaluaciones/$id', data);

  static Future<void> deleteEvaluacion(int id) async =>
      await _delete('/evaluaciones/$id');

  // ── Preguntas ─────────────────────────────────────────────────────────────
  static Future<List<Map<String, dynamic>>> getPreguntasByEvaluacion(int evaluacionId) async {
    try {
      final data = await _get('/evaluaciones/preguntas/evaluacion/$evaluacionId') as List<dynamic>;
      return List<Map<String, dynamic>>.from(data);
    } catch (_) {
      return [];
    }
  }

  static Future<Map<String, dynamic>> createPregunta(Map<String, dynamic> data) async =>
      await _post('/evaluaciones/preguntas', data) as Map<String, dynamic>;

  static Future<void> updatePregunta(int id, Map<String, dynamic> data) async =>
      await _put('/evaluaciones/preguntas/$id', data);

  static Future<void> deletePregunta(int id) async =>
      await _delete('/evaluaciones/preguntas/$id');

  // ── Opciones ──────────────────────────────────────────────────────────────
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

  // ── Respuestas del estudiante ─────────────────────────────────────────────
  static Future<List<Map<String, dynamic>>> getPreguntas(int evaluacionId) async {
    try {
      final data = await _get('/evaluaciones/preguntas/evaluacion/$evaluacionId') as List<dynamic>;
      return List<Map<String, dynamic>>.from(data);
    } catch (_) {
      return [];
    }
  }

  static Future<void> submitRespuestasEstudiante({
    required int evaluacionId,
    required int estudianteId,
    required List<Map<String, dynamic>> respuestas,
  }) async =>
      await _post('/evaluaciones/respuestas/submit', {
        'evaluacion_id': evaluacionId,
        'estudiante_id': estudianteId,
        'respuestas': respuestas,
      });

  static Future<List<Map<String, dynamic>>> getResultadosEstudiante(int estudianteId) async {
    try {
      final data = await _get('/evaluaciones/resultados/estudiante/$estudianteId') as List<dynamic>;
      return List<Map<String, dynamic>>.from(data);
    } catch (_) {
      return [];
    }
  }

  // ==================== INSCRIPCIONES ====================
  static Future<List<Map<String, dynamic>>> getInscripciones() async {
    final data = await _get('/inscripciones') as List<dynamic>;
    return data.cast<Map<String, dynamic>>();
  }

  static Future<List<Map<String, dynamic>>> getInscripcionesByEstudiante(int estudianteId) async {
    final data = await _get('/inscripciones/estudiante/$estudianteId') as List<dynamic>;
    return data.cast<Map<String, dynamic>>();
  }

  static Future<Map<String, dynamic>> createInscripcion(Map<String, dynamic> data) async =>
      await _post('/inscripciones', data) as Map<String, dynamic>;

  static Future<void> updateInscripcion(int id, Map<String, dynamic> data) async =>
      await _put('/inscripciones/$id', data);

  static Future<void> deleteInscripcion(int id) async =>
      await _delete('/inscripciones/$id');

  // ==================== REPORTES ====================
  static Future<List<Map<String, dynamic>>> getReportesAdmin() async {
    try {
      final data = await _get('/evaluaciones/reportes/admin') as List<dynamic>;
      return List<Map<String, dynamic>>.from(data);
    } catch (_) {
      return [];
    }
  }

  static Future<List<Map<String, dynamic>>> getReportesEstudiante(int estudianteId) async {
    try {
      final data = await _get('/evaluaciones/reportes/estudiante/$estudianteId') as List<dynamic>;
      return List<Map<String, dynamic>>.from(data);
    } catch (_) {
      return [];
    }
  }

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