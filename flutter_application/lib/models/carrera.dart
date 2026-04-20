class Carrera {
  final int? carreraId;
  final String? nombre;
  final String? descripcion;
  final int? duracionAnos;

  Carrera({
    this.carreraId,
    this.nombre,
    this.descripcion,
    this.duracionAnos,
  });

  factory Carrera.fromJson(Map<String, dynamic> json) {
    return Carrera(
      carreraId: json['carrera_id'] as int? ?? json['id'] as int?,
      nombre: (json['nombre'] ?? '').toString(),
      descripcion: json['descripcion']?.toString(),
      duracionAnos: json['duracion_anos'] as int?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'nombre': nombre,
      'descripcion': descripcion,
      'duracion_anos': duracionAnos,
    };
  }
}
