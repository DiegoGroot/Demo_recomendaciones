import 'package:flutter/material.dart';
import '../models/calificacion.dart';
import '../models/estudiante.dart';
import '../models/materia.dart';
import '../services/api_service.dart';

class CalificacionesScreen extends StatefulWidget {
  const CalificacionesScreen({super.key});

  @override
  State<CalificacionesScreen> createState() => _CalificacionesScreenState();
}

class _CalificacionesScreenState extends State<CalificacionesScreen> {
  bool _loading = true;
  String? _error;

  List<Calificacion> _cals = [];
  List<Estudiante> _estudiantes = [];
  List<Materia> _materias = [];
  String _busqueda = '';

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final r = await Future.wait([
        ApiService.getCalificaciones(),
        ApiService.getEstudiantes(),
        ApiService.getMaterias(),
      ]);
      if (!mounted) return;
      setState(() {
        _cals        = r[0] as List<Calificacion>;
        _estudiantes = r[1] as List<Estudiante>;
        _materias    = r[2] as List<Materia>;
        _loading     = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() { _error = e.toString(); _loading = false; });
    }
  }

  List<Calificacion> get _filtradas {
    if (_busqueda.isEmpty) return _cals;
    final q = _busqueda.toLowerCase();
    return _cals.where((c) {
      final est = _nombreEst(c.estudianteId).toLowerCase();
      final mat = _nombreMat(c.materiaId).toLowerCase();
      return est.contains(q) || mat.contains(q);
    }).toList();
  }

  String _nombreEst(int id) {
    try { return _estudiantes.firstWhere((e) => e.estudianteId == id).nombre; }
    catch (_) { return 'Est. $id'; }
  }

  String _nombreMat(int id) {
    try { return _materias.firstWhere((m) => m.materiaId == id).nombre; }
    catch (_) { return 'Mat. $id'; }
  }

  /// FIX: devuelve solo las materias de la carrera del estudiante seleccionado.
  /// Si el estudiante no tiene carrera asignada, muestra todas.
  List<Materia> _materiasParaEstudiante(int? estudianteId) {
    if (estudianteId == null) return _materias;
    try {
      final est = _estudiantes.firstWhere((e) => e.estudianteId == estudianteId);
      if (est.carreraId == null) return _materias;
      final filtradas = _materias.where((m) => m.carreraId == est.carreraId).toList();
      return filtradas.isNotEmpty ? filtradas : _materias;
    } catch (_) {
      return _materias;
    }
  }

  Future<void> _generarRecomendacion(Calificacion cal) async {
    if (cal.calificacionId == null) return;
    try {
      await ApiService.generarRecomendacion(cal.calificacionId!);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('✅ Recomendación generada correctamente'),
          backgroundColor: Colors.green));
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text('Error al generar recomendación: $e'),
          backgroundColor: Colors.red));
    }
  }

  void _confirmDelete(Calificacion cal) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Eliminar calificación'),
        content: Text(
            '¿Eliminar la calificación de ${_nombreEst(cal.estudianteId)} en ${_nombreMat(cal.materiaId)}?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancelar')),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(ctx);
              try {
                await ApiService.deleteCalificacion(cal.calificacionId!);
                if (!mounted) return;
                ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                    content: Text('Calificación eliminada'),
                    backgroundColor: Colors.orange));
                _load();
              } catch (e) {
                if (!mounted) return;
                ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Error: $e'), backgroundColor: Colors.red));
              }
            },
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            child: const Text('Eliminar', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }

  void _showForm([Calificacion? cal]) {
    // Estado reactivo para manejar el cambio de estudiante → actualizar lista de materias
    int? estId = cal?.estudianteId ??
        (_estudiantes.isNotEmpty ? _estudiantes.first.estudianteId : null);

    // FIX: calcular materias disponibles desde el inicio según el estudiante
    List<Materia> materiasDisponibles = _materiasParaEstudiante(estId);

    int? matId = cal?.materiaId;
    // Si la materia guardada no está en las disponibles, resetear
    if (matId != null && !materiasDisponibles.any((m) => m.materiaId == matId)) {
      matId = materiasDisponibles.isNotEmpty ? materiasDisponibles.first.materiaId : null;
    } else if (matId == null && materiasDisponibles.isNotEmpty) {
      matId = materiasDisponibles.first.materiaId;
    }

    int numParciales = cal?.numParciales ?? 2;
    String estado = cal?.estado ?? 'en_curso';

    final p1Ctrl  = TextEditingController(text: cal?.notaParcial1?.toString() ?? '');
    final p2Ctrl  = TextEditingController(text: cal?.notaParcial2?.toString() ?? '');
    final p3Ctrl  = TextEditingController(text: cal?.notaParcial3?.toString() ?? '');
    final fnCtrl  = TextEditingController(text: cal?.notaFinal?.toString() ?? '');
    final semCtrl = TextEditingController(text: cal?.semestre?.toString() ?? '1');
    final obsCtrl = TextEditingController(text: cal?.observaciones ?? '');
    bool saving = false;

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setS) => AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          title: Text(cal == null ? 'Nueva Calificación' : 'Editar Calificación',
              style: const TextStyle(fontWeight: FontWeight.bold)),
          content: SizedBox(
            width: 480,
            child: SingleChildScrollView(
              child: Column(mainAxisSize: MainAxisSize.min, children: [

                // ── Estudiante ──────────────────────────────────────────────
                _label('Estudiante *'),
                DropdownButtonFormField<int>(
                  initialValue: estId,
                  decoration: _deco('Selecciona estudiante', Icons.person),
                  items: _estudiantes
                      .map((e) => DropdownMenuItem(
                          value: e.estudianteId,
                          child: Text(e.nombre, overflow: TextOverflow.ellipsis)))
                      .toList(),
                  onChanged: cal == null
                      ? (v) => setS(() {
                            estId = v;
                            // FIX: cuando cambia el estudiante, recalcular materias
                            materiasDisponibles = _materiasParaEstudiante(v);
                            // Resetear materia si la actual no pertenece a la nueva carrera
                            if (!materiasDisponibles.any((m) => m.materiaId == matId)) {
                              matId = materiasDisponibles.isNotEmpty
                                  ? materiasDisponibles.first.materiaId
                                  : null;
                            }
                          })
                      : null,
                ),
                const SizedBox(height: 12),

                // ── Materia (filtrada por carrera del estudiante) ───────────
                _label('Materia *'),
                // FIX: banner informativo con cuántas materias hay disponibles
                if (materiasDisponibles.isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 6),
                    child: Row(children: [
                      Icon(Icons.info_outline, size: 13, color: Colors.indigo.shade400),
                      const SizedBox(width: 4),
                      Text(
                        '${materiasDisponibles.length} materia(s) disponibles para este programa',
                        style: TextStyle(fontSize: 11, color: Colors.indigo.shade400),
                      ),
                    ]),
                  ),
                DropdownButtonFormField<int>(
                  initialValue: materiasDisponibles.any((m) => m.materiaId == matId) ? matId : null,
                  decoration: _deco('Selecciona materia', Icons.book),
                  items: materiasDisponibles
                      .map((m) => DropdownMenuItem(
                          value: m.materiaId,
                          child: Text(m.nombre, overflow: TextOverflow.ellipsis)))
                      .toList(),
                  onChanged: cal == null ? (v) => setS(() => matId = v) : null,
                ),
                const SizedBox(height: 12),

                // ── Número de parciales ─────────────────────────────────────
                _label('Número de Parciales'),
                DropdownButtonFormField<int>(
                  initialValue: numParciales,
                  decoration: _deco('Parciales de la materia', Icons.format_list_numbered),
                  items: const [
                    DropdownMenuItem(value: 1, child: Text('1 Parcial')),
                    DropdownMenuItem(value: 2, child: Text('2 Parciales')),
                    DropdownMenuItem(value: 3, child: Text('3 Parciales')),
                  ],
                  onChanged: (v) => setS(() => numParciales = v ?? 2),
                ),
                const SizedBox(height: 12),

                // ── Notas parciales ─────────────────────────────────────────
                Row(children: [
                  Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    _label('Parcial 1'),
                    _numField(p1Ctrl, 'ej: 8.5'),
                  ])),
                  if (numParciales >= 2) ...[
                    const SizedBox(width: 10),
                    Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      _label('Parcial 2'),
                      _numField(p2Ctrl, 'ej: 7.0'),
                    ])),
                  ],
                  if (numParciales >= 3) ...[
                    const SizedBox(width: 10),
                    Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      _label('Parcial 3'),
                      _numField(p3Ctrl, 'ej: 9.0'),
                    ])),
                  ],
                ]),
                const SizedBox(height: 8),

                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.blue.shade50,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Row(children: [
                    Icon(Icons.info_outline, size: 14, color: Colors.blue.shade700),
                    const SizedBox(width: 6),
                    Text('Escala: 0 a 10  •  Aprobado: ≥ 6.0',
                        style: TextStyle(fontSize: 11, color: Colors.blue.shade700)),
                  ]),
                ),
                const SizedBox(height: 12),

                // ── Nota Final y Semestre ───────────────────────────────────
                Row(children: [
                  Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    _label('Nota Final *'),
                    _numField(fnCtrl, 'ej: 8.0'),
                  ])),
                  const SizedBox(width: 10),
                  Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    _label('Semestre'),
                    _numField(semCtrl, 'ej: 1', isInt: true),
                  ])),
                ]),
                const SizedBox(height: 12),

                // ── Estado ─────────────────────────────────────────────────
                _label('Estado'),
                DropdownButtonFormField<String>(
                  initialValue: estado,
                  decoration: _deco('Estado', Icons.info_outline),
                  items: const [
                    DropdownMenuItem(value: 'en_curso',   child: Text('En curso')),
                    DropdownMenuItem(value: 'aprobado',   child: Text('✅ Aprobado')),
                    DropdownMenuItem(value: 'reprobado',  child: Text('❌ Reprobado')),
                  ],
                  onChanged: (v) => setS(() => estado = v ?? estado),
                ),
                const SizedBox(height: 12),

                // ── Observaciones ───────────────────────────────────────────
                _label('Observaciones del Maestro'),
                TextField(
                  controller: obsCtrl,
                  maxLines: 3,
                  decoration: InputDecoration(
                    hintText: 'Escribe observaciones sobre el desempeño del alumno...',
                    hintStyle: TextStyle(fontSize: 12, color: Colors.grey.shade400),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                    enabledBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(10),
                        borderSide: BorderSide(color: Colors.grey.shade300)),
                    focusedBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(10),
                        borderSide: BorderSide(color: Colors.indigo.shade400, width: 2)),
                  ),
                ),

                if (saving) ...[
                  const SizedBox(height: 16),
                  const LinearProgressIndicator(),
                ],
              ]),
            ),
          ),
          actions: [
            TextButton(
              onPressed: saving ? null : () => Navigator.pop(ctx),
              child: const Text('Cancelar'),
            ),
            ElevatedButton.icon(
              onPressed: saving
                  ? null
                  : () async {
                      if (estId == null || matId == null || fnCtrl.text.trim().isEmpty) {
                        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                            content: Text('Estudiante, materia y nota final son obligatorios'),
                            backgroundColor: Colors.red));
                        return;
                      }

                      final notaFinal = double.tryParse(fnCtrl.text);
                      if (notaFinal == null || notaFinal < 0 || notaFinal > 10) {
                        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                            content: Text('La nota final debe estar entre 0 y 10'),
                            backgroundColor: Colors.red));
                        return;
                      }

                      final p1 = double.tryParse(p1Ctrl.text);
                      final p2 = double.tryParse(p2Ctrl.text);
                      final p3 = double.tryParse(p3Ctrl.text);
                      for (final nota in [p1, p2, p3]) {
                        if (nota != null && (nota < 0 || nota > 10)) {
                          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                              content: Text('Las notas deben estar entre 0 y 10'),
                              backgroundColor: Colors.red));
                          return;
                        }
                      }

                      setS(() => saving = true);
                      try {
                        final body = <String, dynamic>{
                          'estudiante_id': estId!,
                          'materia_id': matId!,
                          if (p1 != null) 'parcial1': p1,
                          if (numParciales >= 2 && p2 != null) 'parcial2': p2,
                          if (numParciales >= 3 && p3 != null) 'parcial3': p3,
                          'nota_final': notaFinal,
                          'semestre': int.tryParse(semCtrl.text) ?? 1,
                          'estado': estado,
                          if (obsCtrl.text.trim().isNotEmpty) 'observaciones': obsCtrl.text.trim(),
                          'num_parciales': numParciales,
                        };
                        if (cal != null) {
                          await ApiService.updateCalificacion(cal.calificacionId!, body);
                        } else {
                          await ApiService.createCalificacion(body);
                        }
                        if (!ctx.mounted) return;
                        Navigator.pop(ctx);
                        if (context.mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                              content: Text(cal == null
                                  ? 'Calificación creada ✅'
                                  : 'Calificación actualizada ✅'),
                              backgroundColor: Colors.green));
                          _load();
                        }
                      } catch (e) {
                        setS(() => saving = false);
                        if (context.mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(content: Text('Error: $e'), backgroundColor: Colors.red));
                        }
                      }
                    },
              icon: const Icon(Icons.save),
              label: Text(cal == null ? 'Guardar' : 'Actualizar'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.indigo.shade700,
                foregroundColor: Colors.white,
              ),
            ),
          ],
        ),
      ),
    );
  }

  InputDecoration _deco(String hint, IconData icon) => InputDecoration(
        hintText: hint,
        prefixIcon: Icon(icon, size: 18),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
        enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(10),
            borderSide: BorderSide(color: Colors.grey.shade300)),
        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      );

  Widget _label(String text) => Padding(
        padding: const EdgeInsets.only(bottom: 4),
        child: Text(text,
            style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w600,
                color: Colors.grey.shade700)),
      );

  Widget _numField(TextEditingController ctrl, String hint, {bool isInt = false}) =>
      TextField(
        controller: ctrl,
        keyboardType: const TextInputType.numberWithOptions(decimal: true),
        decoration: InputDecoration(
          hintText: hint,
          hintStyle: TextStyle(fontSize: 12, color: Colors.grey.shade400),
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
          enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(10),
              borderSide: BorderSide(color: Colors.grey.shade300)),
          contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
        ),
      );

  Color _colorNota(double? nota) {
    if (nota == null) return Colors.grey;
    if (nota >= 8) return Colors.green.shade700;
    if (nota >= 6) return Colors.orange.shade700;
    return Colors.red.shade700;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Calificaciones (${_filtradas.length} registros)'),
        backgroundColor: Colors.indigo.shade700,
        foregroundColor: Colors.white,
        elevation: 0,
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _load),
          IconButton(
            icon: const Icon(Icons.add),
            tooltip: 'Agregar',
            onPressed: () => _showForm(),
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                  Icon(Icons.error_outline, size: 64, color: Colors.red.shade300),
                  const SizedBox(height: 16),
                  Text('Error: $_error'),
                  const SizedBox(height: 16),
                  ElevatedButton.icon(
                      onPressed: _load,
                      icon: const Icon(Icons.refresh),
                      label: const Text('Reintentar')),
                ]))
              : Column(children: [
                  Padding(
                    padding: const EdgeInsets.all(12),
                    child: TextField(
                      onChanged: (v) => setState(() => _busqueda = v),
                      decoration: InputDecoration(
                        hintText: 'Buscar por estudiante o materia...',
                        prefixIcon: const Icon(Icons.search),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                        filled: true,
                        fillColor: Colors.grey.shade50,
                        suffixText: '${_filtradas.length} registros',
                      ),
                    ),
                  ),
                  Expanded(
                    child: _filtradas.isEmpty
                        ? Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                            Icon(Icons.grade_outlined, size: 64, color: Colors.grey.shade300),
                            const SizedBox(height: 16),
                            const Text('No hay calificaciones'),
                            const SizedBox(height: 8),
                            ElevatedButton.icon(
                              onPressed: () => _showForm(),
                              icon: const Icon(Icons.add),
                              label: const Text('Agregar primera'),
                              style: ElevatedButton.styleFrom(
                                  backgroundColor: Colors.indigo.shade700,
                                  foregroundColor: Colors.white),
                            ),
                          ]))
                        : RefreshIndicator(
                            onRefresh: _load,
                            child: ListView.builder(
                              padding: const EdgeInsets.symmetric(horizontal: 12),
                              itemCount: _filtradas.length,
                              itemBuilder: (ctx, i) => _calCard(_filtradas[i]),
                            ),
                          ),
                  ),
                ]),
      floatingActionButton: FloatingActionButton.extended(
        heroTag: 'fab_calificaciones',
        onPressed: () => _showForm(),
        backgroundColor: Colors.indigo.shade700,
        icon: const Icon(Icons.add),
        label: const Text('Agregar'),
      ),
    );
  }

  Widget _calCard(Calificacion c) {
    final color = _colorNota(c.notaFinal);
    final numP = c.numParciales;

    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Container(
              width: 50, height: 50,
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.12),
                shape: BoxShape.circle,
                border: Border.all(color: color, width: 2),
              ),
              child: Center(
                child: Text(
                  c.notaFinal?.toStringAsFixed(1) ?? '-',
                  style: TextStyle(fontWeight: FontWeight.bold, color: color, fontSize: 15),
                ),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(c.estudianteNombre ?? _nombreEst(c.estudianteId),
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
              Text(c.materiaNombre ?? _nombreMat(c.materiaId),
                  style: TextStyle(fontSize: 13, color: Colors.grey.shade600)),
            ])),
            _estadoBadge(c.estado),
          ]),
          const SizedBox(height: 10),
          Wrap(spacing: 8, runSpacing: 6, children: [
            if (c.notaParcial1 != null) _notaChip('P1', c.notaParcial1!),
            if (numP >= 2 && c.notaParcial2 != null) _notaChip('P2', c.notaParcial2!),
            if (numP >= 3 && c.notaParcial3 != null) _notaChip('P3', c.notaParcial3!),
            if (c.semestre != null) _infoChip('Sem. ${c.semestre}', Colors.purple),
          ]),
          if (c.observaciones != null && c.observaciones!.isNotEmpty) ...[
            const SizedBox(height: 8),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: Colors.amber.shade50,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.amber.shade200),
              ),
              child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Icon(Icons.comment, size: 14, color: Colors.amber.shade700),
                const SizedBox(width: 6),
                Expanded(child: Text(c.observaciones!,
                    style: TextStyle(fontSize: 12, color: Colors.amber.shade900))),
              ]),
            ),
          ],
          const SizedBox(height: 10),
          Row(mainAxisAlignment: MainAxisAlignment.end, children: [
            if (c.estado == 'aprobado' || c.estado == 'reprobado')
              TextButton.icon(
                onPressed: () => _generarRecomendacion(c),
                icon: Icon(Icons.lightbulb, size: 16, color: Colors.amber.shade700),
                label: Text('Generar Rec.',
                    style: TextStyle(fontSize: 12, color: Colors.amber.shade700)),
              ),
            IconButton(
              icon: const Icon(Icons.edit, size: 18),
              onPressed: () => _showForm(c),
              tooltip: 'Editar',
              constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
            ),
            IconButton(
              icon: const Icon(Icons.delete, size: 18),
              onPressed: () => _confirmDelete(c),
              tooltip: 'Eliminar',
              constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
              color: Colors.red.shade400,
            ),
          ]),
        ]),
      ),
    );
  }

  Widget _notaChip(String label, double nota) {
    final color = nota >= 8 ? Colors.green : nota >= 6 ? Colors.orange : Colors.red;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withValues(alpha: 0.4)),
      ),
      child: Text('$label: ${nota.toStringAsFixed(1)}',
          style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: color.shade700)),
    );
  }

  Widget _infoChip(String text, MaterialColor color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Text(text,
          style: TextStyle(fontSize: 11, color: color.shade700, fontWeight: FontWeight.w500)),
    );
  }

  Widget _estadoBadge(String estado) {
    final color = estado == 'aprobado'
        ? Colors.green
        : estado == 'reprobado'
            ? Colors.red
            : Colors.orange;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withValues(alpha: 0.4)),
      ),
      child: Text(
        estado == 'aprobado' ? '✅ Aprobado'
            : estado == 'reprobado' ? '❌ Reprobado'
            : '⏳ En curso',
        style: TextStyle(fontSize: 10, color: color, fontWeight: FontWeight.bold),
      ),
    );
  }
}