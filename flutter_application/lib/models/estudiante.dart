class Estudiante {
  final int? estudianteId;
  final String nombre;
  final String correo;
  final String? contrasena;
  final int? carreraId;
  final String? carrera;
  final double? promedioGeneral;

  Estudiante({
    this.estudianteId,
    required this.nombre,
    required this.correo,
    this.contrasena,
    this.carreraId,
    this.carrera,
    this.promedioGeneral,
  });

  factory Estudiante.fromJson(Map<String, dynamic> json) {
    return Estudiante(
      estudianteId: json['estudiante_id'] as int?,
      nombre: json['nombre'] as String,
      correo: json['correo'] as String,
      contrasena: json['contrasena'] as String?,
      carreraId: json['carrera_id'] as int?,
      carrera: json['carrera'] as String?,
      promedioGeneral: (json['promedio_general'] as num?)?.toDouble(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'nombre': nombre,
      'correo': correo,
      'contrasena': contrasena,
      'carrera_id': carreraId,
    };
  }
}
