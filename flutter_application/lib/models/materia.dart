class Materia {
  final int? materiaId;
  final String nombre;
  final String codigo;
  final int? carreraId;
  final int creditos;    // NOT NULL en DB
  final String? descripcion;
  final int semestre;    // NOT NULL en DB
  final String? contenido;

  Materia({
    this.materiaId,
    required this.nombre,
    required this.codigo,
    this.carreraId,
    this.creditos = 3,
    this.descripcion,
    this.semestre = 1,
    this.contenido,
  });

  factory Materia.fromJson(Map<String, dynamic> json) {
    return Materia(
      materiaId: json['materia_id'] as int?,
      nombre:    json['nombre'] as String,
      codigo:    json['codigo'] as String,
      carreraId: json['carrera_id'] as int?,
      creditos:  _parseInt(json['creditos']) ?? 3,
      descripcion: json['descripcion'] as String?,
      semestre:  _parseInt(json['semestre']) ?? 1,
      contenido: json['contenido'] as String?,
    );
  }

  static int? _parseInt(dynamic value) {
    if (value == null) return null;
    if (value is int) return value;
    if (value is double) return value.toInt();
    if (value is String) return int.tryParse(value);
    return null;
  }

  Map<String, dynamic> toJson() {
    return {
      'nombre':    nombre,
      'codigo':    codigo,
      'carrera_id': carreraId,
      'creditos':  creditos,    // siempre int, nunca null
      'semestre':  semestre,    // siempre int, nunca null
      if (descripcion != null) 'descripcion': descripcion,
      'contenido': contenido,   // null = borrar syllabus
    };
  }
}