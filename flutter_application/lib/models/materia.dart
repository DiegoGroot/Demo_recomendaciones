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
      creditos: json['creditos'] as int?,
      descripcion: json['descripcion'] as String?,
      semestre: json['semestre'] as int?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'nombre': nombre,
      'codigo': codigo,
      'carrera_id': carreraId,
      'creditos': creditos,
      'descripcion': descripcion,
      'semestre': semestre,
    };
  }
}
