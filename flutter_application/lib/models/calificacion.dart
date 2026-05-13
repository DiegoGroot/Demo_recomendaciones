class Calificacion {
  final int? calificacionId;
  final int estudianteId;
  final int materiaId;
  final double? notaParcial1;
  final double? notaParcial2;
  final double? notaParcial3;
  final double? notaFinal;
  final String estado;
  final int? semestre;
  final String? materiaNombre;
  final String? estudianteNombre;
  final String? observaciones;
  final int numParciales;

  Calificacion({
    this.calificacionId,
    required this.estudianteId,
    required this.materiaId,
    this.notaParcial1,
    this.notaParcial2,
    this.notaParcial3,
    this.notaFinal,
    this.estado = 'en_curso',
    this.semestre,
    this.materiaNombre,
    this.estudianteNombre,
    this.observaciones,
    this.numParciales = 2,
  });

  factory Calificacion.fromJson(Map<String, dynamic> json) => Calificacion(
      calificacionId: json['calificacion_id'] as int?,
      estudianteId: json['estudiante_id'] as int,
      materiaId: json['materia_id'] as int,
      notaParcial1: (json['nota_parcial1'] as num?)?.toDouble(),
      notaParcial2: (json['nota_parcial2'] as num?)?.toDouble(),
      notaParcial3: (json['nota_parcial3'] as num?)?.toDouble(),
      notaFinal: (json['nota_final'] as num?)?.toDouble(),
      estado: json['estado'] as String? ?? 'en_curso',
      semestre: json['semestre'] as int?,
      materiaNombre: json['materia_nombre'] as String?,
      estudianteNombre: json['estudiante_nombre'] as String?,
      observaciones: json['observaciones'] as String?,
      numParciales: (json['num_parciales'] as int?) ?? 2,
    );

  Map<String, dynamic> toJson() => {
      'estudiante_id': estudianteId,
      'materia_id': materiaId,
      if (notaParcial1 != null) 'parcial1': notaParcial1,
      if (notaParcial2 != null) 'parcial2': notaParcial2,
      if (notaParcial3 != null) 'parcial3': notaParcial3,
      if (notaFinal != null) 'nota_final': notaFinal,
      'estado': estado,
      if (semestre != null) 'semestre': semestre,
      if (observaciones != null) 'observaciones': observaciones,
      'num_parciales': numParciales,
    };
}