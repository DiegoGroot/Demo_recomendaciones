import 'package:http/http.dart' as http;
import 'dart:convert';
import '../models/carrera.dart';
import '../models/materia.dart';
import '../models/estudiante.dart';
import '../models/calificacion.dart';
import '../models/recomendacion.dart';

class ApiService {
  static const String baseUrl = 'http://localhost:8000/api';
  static const int timeoutSeconds = 10;

  // ==================== CARRERAS ====================
  static Future<List<Carrera>> getCarreras() async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/carreras'))
          .timeout(const Duration(seconds: timeoutSeconds));
      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body) as List<dynamic>;
        return data
            .map((c) => Carrera.fromJson(c as Map<String, dynamic>))
            .toList();
      }
      throw Exception('Error al cargar carreras: ${response.statusCode}');
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  static Future<Carrera> createCarrera(Carrera carrera) async {
    try {
      final response = await http
          .post(
            Uri.parse('$baseUrl/carreras'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(carrera.toJson()),
          )
          .timeout(const Duration(seconds: timeoutSeconds));
      if (response.statusCode == 201 || response.statusCode == 200) {
        return Carrera.fromJson(
            jsonDecode(response.body) as Map<String, dynamic>);
      }
      throw Exception('Error al crear carrera: ${response.statusCode}');
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  static Future<void> updateCarrera(int id, Carrera carrera) async {
    try {
      final response = await http
          .put(
            Uri.parse('$baseUrl/carreras/$id'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(carrera.toJson()),
          )
          .timeout(const Duration(seconds: timeoutSeconds));
      if (response.statusCode != 200) {
        throw Exception('Error al actualizar carrera: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  static Future<void> deleteCarrera(int id) async {
    try {
      final response = await http
          .delete(Uri.parse('$baseUrl/carreras/$id'))
          .timeout(const Duration(seconds: timeoutSeconds));
      if (response.statusCode != 200) {
        throw Exception('Error al eliminar carrera: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  // ==================== MATERIAS ====================
  static Future<List<Materia>> getMaterias() async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/materias'))
          .timeout(const Duration(seconds: timeoutSeconds));
      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body) as List<dynamic>;
        return data
            .map((m) => Materia.fromJson(m as Map<String, dynamic>))
            .toList();
      }
      throw Exception('Error al cargar materias: ${response.statusCode}');
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  static Future<List<Materia>> getMateriasByCarrera(int carreraId) async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/materias?carrera_id=$carreraId'))
          .timeout(const Duration(seconds: timeoutSeconds));
      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body) as List<dynamic>;
        return data
            .map((m) => Materia.fromJson(m as Map<String, dynamic>))
            .toList();
      }
      throw Exception('Error al cargar materias: ${response.statusCode}');
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  static Future<Materia> createMateria(Materia materia) async {
    try {
      final response = await http
          .post(
            Uri.parse('$baseUrl/materias'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(materia.toJson()),
          )
          .timeout(const Duration(seconds: timeoutSeconds));
      if (response.statusCode == 201 || response.statusCode == 200) {
        return Materia.fromJson(
            jsonDecode(response.body) as Map<String, dynamic>);
      }
      throw Exception('Error al crear materia: ${response.statusCode}');
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  static Future<void> updateMateria(int id, Materia materia) async {
    try {
      final response = await http
          .put(
            Uri.parse('$baseUrl/materias/$id'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(materia.toJson()),
          )
          .timeout(const Duration(seconds: timeoutSeconds));
      if (response.statusCode != 200) {
        throw Exception('Error al actualizar materia: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  static Future<void> deleteMateria(int id) async {
    try {
      final response = await http
          .delete(Uri.parse('$baseUrl/materias/$id'))
          .timeout(const Duration(seconds: timeoutSeconds));
      if (response.statusCode != 200) {
        throw Exception('Error al eliminar materia: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  // ==================== ESTUDIANTES ====================
  static Future<Map<String, dynamic>> login(
      String correo, String contrasena) async {
    try {
      final response = await http
          .post(
            Uri.parse('$baseUrl/estudiantes/login'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({'correo': correo, 'contrasena': contrasena}),
          )
          .timeout(const Duration(seconds: timeoutSeconds));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        return data;
      }
      throw Exception('Error al iniciar sesión: ${response.statusCode}');
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  static Future<List<Estudiante>> getEstudiantes() async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/estudiantes'))
          .timeout(const Duration(seconds: timeoutSeconds));
      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body) as List<dynamic>;
        return data
            .map((e) => Estudiante.fromJson(e as Map<String, dynamic>))
            .toList();
      }
      throw Exception('Error al cargar estudiantes: ${response.statusCode}');
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  static Future<Estudiante> getEstudianteById(int id) async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/estudiantes/$id'))
          .timeout(const Duration(seconds: timeoutSeconds));
      if (response.statusCode == 200) {
        return Estudiante.fromJson(
            jsonDecode(response.body) as Map<String, dynamic>);
      }
      throw Exception('Estudiante no encontrado: ${response.statusCode}');
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  static Future<Estudiante> createEstudiante(Estudiante estudiante) async {
    try {
      final response = await http
          .post(
            Uri.parse('$baseUrl/estudiantes'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(estudiante.toJson()),
          )
          .timeout(const Duration(seconds: timeoutSeconds));
      if (response.statusCode == 201 || response.statusCode == 200) {
        return Estudiante.fromJson(
            jsonDecode(response.body) as Map<String, dynamic>);
      }
      throw Exception('Error al crear estudiante: ${response.statusCode}');
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  static Future<void> updateEstudiante(int id, Estudiante estudiante) async {
    try {
      final response = await http
          .put(
            Uri.parse('$baseUrl/estudiantes/$id'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(estudiante.toJson()),
          )
          .timeout(const Duration(seconds: timeoutSeconds));
      if (response.statusCode != 200) {
        throw Exception(
            'Error al actualizar estudiante: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  static Future<void> deleteEstudiante(int id) async {
    try {
      final response = await http
          .delete(Uri.parse('$baseUrl/estudiantes/$id'))
          .timeout(const Duration(seconds: timeoutSeconds));
      if (response.statusCode != 200) {
        throw Exception('Error al eliminar estudiante: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  // ==================== CALIFICACIONES ====================
  static Future<List<Calificacion>> getCalificaciones() async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/calificaciones'))
          .timeout(const Duration(seconds: timeoutSeconds));
      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body) as List<dynamic>;
        return data
            .map((c) => Calificacion.fromJson(c as Map<String, dynamic>))
            .toList();
      }
      throw Exception('Error al cargar calificaciones: ${response.statusCode}');
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  static Future<List<Calificacion>> getCalificacionesByEstudiante(
      int estudianteId) async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/calificaciones?estudiante_id=$estudianteId'))
          .timeout(const Duration(seconds: timeoutSeconds));
      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body) as List<dynamic>;
        return data
            .map((c) => Calificacion.fromJson(c as Map<String, dynamic>))
            .toList();
      }
      throw Exception('Error al cargar calificaciones: ${response.statusCode}');
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  static Future<Calificacion> createCalificacion(
      Calificacion calificacion) async {
    try {
      final response = await http
          .post(
            Uri.parse('$baseUrl/calificaciones'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(calificacion.toJson()),
          )
          .timeout(const Duration(seconds: timeoutSeconds));
      if (response.statusCode == 201 || response.statusCode == 200) {
        return Calificacion.fromJson(
            jsonDecode(response.body) as Map<String, dynamic>);
      }
      throw Exception('Error al crear calificación: ${response.statusCode}');
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  static Future<void> updateCalificacion(
      int id, Calificacion calificacion) async {
    try {
      final response = await http
          .put(
            Uri.parse('$baseUrl/calificaciones/$id'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(calificacion.toJson()),
          )
          .timeout(const Duration(seconds: timeoutSeconds));
      if (response.statusCode != 200) {
        throw Exception(
            'Error al actualizar calificación: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  static Future<void> deleteCalificacion(int id) async {
    try {
      final response = await http
          .delete(Uri.parse('$baseUrl/calificaciones/$id'))
          .timeout(const Duration(seconds: timeoutSeconds));
      if (response.statusCode != 200) {
        throw Exception(
            'Error al eliminar calificación: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  // ==================== RECOMENDACIONES ====================
  static Future<List<Recomendacion>> getRecomendaciones() async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/recomendaciones'))
          .timeout(const Duration(seconds: timeoutSeconds));
      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body) as List<dynamic>;
        return data
            .map((r) => Recomendacion.fromJson(r as Map<String, dynamic>))
            .toList();
      }
      throw Exception(
          'Error al cargar recomendaciones: ${response.statusCode}');
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  static Future<List<Recomendacion>> getRecomendacionesByEstudiante(
      int estudianteId) async {
    try {
      final response = await http
          .get(
              Uri.parse('$baseUrl/recomendaciones?estudiante_id=$estudianteId'))
          .timeout(const Duration(seconds: timeoutSeconds));
      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body) as List<dynamic>;
        return data
            .map((r) => Recomendacion.fromJson(r as Map<String, dynamic>))
            .toList();
      }
      throw Exception(
          'Error al cargar recomendaciones: ${response.statusCode}');
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  static Future<List<Recomendacion>> getRecomendacionesByPrioridad(
      String prioridad) async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/recomendaciones?prioridad=$prioridad'))
          .timeout(const Duration(seconds: timeoutSeconds));
      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body) as List<dynamic>;
        return data
            .map((r) => Recomendacion.fromJson(r as Map<String, dynamic>))
            .toList();
      }
      throw Exception(
          'Error al cargar recomendaciones: ${response.statusCode}');
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  static Future<Recomendacion> createRecomendacion(
      Recomendacion recomendacion) async {
    try {
      final response = await http
          .post(
            Uri.parse('$baseUrl/recomendaciones'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(recomendacion.toJson()),
          )
          .timeout(const Duration(seconds: timeoutSeconds));
      if (response.statusCode == 201 || response.statusCode == 200) {
        return Recomendacion.fromJson(
            jsonDecode(response.body) as Map<String, dynamic>);
      }
      throw Exception('Error al crear recomendación: ${response.statusCode}');
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  static Future<void> updateRecomendacion(
      int id, Recomendacion recomendacion) async {
    try {
      final response = await http
          .put(
            Uri.parse('$baseUrl/recomendaciones/$id'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(recomendacion.toJson()),
          )
          .timeout(const Duration(seconds: timeoutSeconds));
      if (response.statusCode != 200) {
        throw Exception(
            'Error al actualizar recomendación: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  static Future<void> deleteRecomendacion(int id) async {
    try {
      final response = await http
          .delete(Uri.parse('$baseUrl/recomendaciones/$id'))
          .timeout(const Duration(seconds: timeoutSeconds));
      if (response.statusCode != 200) {
        throw Exception(
            'Error al eliminar recomendación: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  // ==================== HEALTH CHECK ====================
  static Future<bool> checkConnection() async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/../'))
          .timeout(const Duration(seconds: timeoutSeconds));
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }
}
