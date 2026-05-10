class Materia {
  final int? materiaId;
  final String nombre;
  final String codigo;
  final int? carreraId;
  final int? creditos;
  final String? descripcion;
  final int? semestre;

  Materia({
    this.materiaId,
    required this.nombre,
    required this.codigo,
    this.carreraId,
    this.creditos,
    this.descripcion,
    this.semestre,
  });

  factory Materia.fromJson(Map<String, dynamic> json) {
    return Materia(
      materiaId: json['materia_id'] as int?,
      nombre: json['nombre'] as String,
      codigo: json['codigo'] as String,
      carreraId: json['carrera_id'] as int?,
      // FIX: MySQL puede devolver creditos/semestre como String en algunos drivers
      creditos: _parseInt(json['creditos']),
      descripcion: json['descripcion'] as String?,
      semestre: _parseInt(json['semestre']),
    );
  }

  /// Convierte int, String numérico o null de forma segura.
  static int? _parseInt(dynamic value) {
    if (value == null) return null;
    if (value is int) return value;
    if (value is double) return value.toInt();
    if (value is String) return int.tryParse(value);
    return null;
  }

  Map<String, dynamic> toJson() {
    return {
      'nombre': nombre,
      'codigo': codigo,
      'carrera_id': carreraId,
      // FIX: solo incluir si no son null para que el backend no sobreescriba con null
      if (creditos != null) 'creditos': creditos,
      if (descripcion != null) 'descripcion': descripcion,
      if (semestre != null) 'semestre': semestre,
    };
  }
}