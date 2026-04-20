class Calificacion {
  final int? calificacionId;
  final int estudianteId;
  final int materiaId;
  final double? notaParcial1;
  final double? notaParcial2;
  final double? notaFinal;
  final String estado;
  final int? semestre;
  final String? materiaNombre;
  final String? estudianteNombre;

  Calificacion({
    this.calificacionId,
    required this.estudianteId,
    required this.materiaId,
    this.notaParcial1,
    this.notaParcial2,
    this.notaFinal,
    this.estado = 'en_curso',
    this.semestre,
    this.materiaNombre,
    this.estudianteNombre,
  });

  factory Calificacion.fromJson(Map<String, dynamic> json) {
    return Calificacion(
      calificacionId: json['calificacion_id'] as int?,
      estudianteId: json['estudiante_id'] as int,
      materiaId: json['materia_id'] as int,
      notaParcial1: (json['nota_parcial1'] as num?)?.toDouble(),
      notaParcial2: (json['nota_parcial2'] as num?)?.toDouble(),
      notaFinal: (json['nota_final'] as num?)?.toDouble(),
      estado: json['estado'] as String? ?? 'en_curso',
      semestre: json['semestre'] as int?,
      materiaNombre: json['materia_nombre'] as String?,
      estudianteNombre: json['estudiante_nombre'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'estudiante_id': estudianteId,
      'materia_id': materiaId,
      'nota_parcial1': notaParcial1,
      'nota_parcial2': notaParcial2,
      'nota_final': notaFinal,
      'estado': estado,
      'semestre': semestre,
    };
  }
}
