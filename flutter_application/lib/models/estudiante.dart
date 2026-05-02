class Estudiante {
  final int? estudianteId;
  final String nombre;
  final String correo;
  final String? contrasena;
  final int? carreraId;
  final String? carrera;
  final double? promedioGeneral;
  final String? rol;
  final int? edad;
  final String? fechaNacimiento;

  Estudiante({
    this.estudianteId,
    required this.nombre,
    required this.correo,
    this.contrasena,
    this.carreraId,
    this.carrera,
    this.promedioGeneral,
    this.rol,
    this.edad,
    this.fechaNacimiento,
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
      rol: json['rol'] as String?,
      edad: json['edad'] as int?,
      fechaNacimiento: json['fecha_nacimiento'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'nombre': nombre,
      'correo': correo,
      if (contrasena != null) 'contrasena': contrasena,
      if (carreraId != null) 'carrera_id': carreraId,
      if (rol != null) 'rol': rol,
      if (edad != null) 'edad': edad,
      if (fechaNacimiento != null) 'fecha_nacimiento': fechaNacimiento,
    };
  }
}
