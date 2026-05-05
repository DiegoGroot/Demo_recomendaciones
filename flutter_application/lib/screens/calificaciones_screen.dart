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
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final r = await Future.wait([
        ApiService.getCalificaciones(),
        ApiService.getEstudiantes(),
        ApiService.getMaterias(),
      ]);
      if (!mounted) return;
      setState(() {
        _cals = r[0] as List<Calificacion>;
        _estudiantes = r[1] as List<Estudiante>;
        _materias = r[2] as List<Materia>;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString();
        _loading = false;
      });
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
    try {
      return _estudiantes.firstWhere((e) => e.estudianteId == id).nombre;
    } catch (_) {
      return 'Est. $id';
    }
  }

  String _nombreMat(int id) {
    try {
      return _materias.firstWhere((m) => m.materiaId == id).nombre;
    } catch (_) {
      return 'Mat. $id';
    }
  }

  Color _colorNota(double? n) {
    if (n == null) return Colors.grey;
    if (n >= 3.5) return Colors.green.shade700;
    if (n >= 2.5) return Colors.orange.shade700;
    return Colors.red.shade700;
  }

  String _estadoLabel(String e) {
    switch (e) {
      case 'aprobado':
        return 'Aprobado ✓';
      case 'reprobado':
        return 'Reprobado ✗';
      case 'en_curso':
        return 'En curso';
      default:
        return e;
    }
  }

  void _abrirFormulario({Calificacion? cal}) {
    int? estId = cal?.estudianteId ??
        (_estudiantes.isNotEmpty ? _estudiantes.first.estudianteId : null);
    int? matId = cal?.materiaId ??
        (_materias.isNotEmpty ? _materias.first.materiaId : null);
    String estado = cal?.estado ?? 'en_curso';
    final p1Ctrl =
        TextEditingController(text: cal?.notaParcial1?.toString() ?? '');
    final p2Ctrl =
        TextEditingController(text: cal?.notaParcial2?.toString() ?? '');
    final fnCtrl =
        TextEditingController(text: cal?.notaFinal?.toString() ?? '');
    final semCtrl =
        TextEditingController(text: cal?.semestre?.toString() ?? '');
    bool saving = false;

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setS) => AlertDialog(
          title: Text(cal == null ? 'Nueva Calificación' : 'Editar Calificación'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // ── Estudiante ────────────────────────────────────────────
                _label('Estudiante *'),
                DropdownButtonFormField<int>(
                  value: estId,
                  decoration: _deco('Selecciona estudiante', Icons.person),
                  items: _estudiantes
                      .map(
                        (e) => DropdownMenuItem(
                          value: e.estudianteId,
                          child: Text(
                            e.nombre,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      )
                      .toList(),
                  onChanged: cal == null
                      ? (v) => setS(() => estId = v)
                      : null,
                ),
                const SizedBox(height: 12),

                // ── Materia ───────────────────────────────────────────────
                _label('Materia *'),
                DropdownButtonFormField<int>(
                  value: matId,
                  decoration: _deco('Selecciona materia', Icons.book),
                  items: _materias
                      .map(
                        (m) => DropdownMenuItem(
                          value: m.materiaId,
                          child: Text(
                            m.nombre,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      )
                      .toList(),
                  onChanged: cal == null
                      ? (v) => setS(() => matId = v)
                      : null,
                ),
                const SizedBox(height: 12),

                // ── Notas ─────────────────────────────────────────────────
                Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          _label('Parcial 1'),
                          _numField(p1Ctrl, 'ej: 3.5'),
                        ],
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          _label('Parcial 2'),
                          _numField(p2Ctrl, 'ej: 4.0'),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),

                Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          _label('Nota Final *'),
                          _numField(fnCtrl, 'ej: 3.8'),
                        ],
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          _label('Semestre'),
                          _numField(semCtrl, 'ej: 1', isInt: true),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),

                // ── Estado ────────────────────────────────────────────────
                _label('Estado'),
                DropdownButtonFormField<String>(
                  value: estado,
                  decoration: _deco('Estado', Icons.info_outline),
                  items: const [
                    DropdownMenuItem(
                      value: 'en_curso',
                      child: Text('En curso'),
                    ),
                    DropdownMenuItem(
                      value: 'aprobado',
                      child: Text('Aprobado'),
                    ),
                    DropdownMenuItem(
                      value: 'reprobado',
                      child: Text('Reprobado'),
                    ),
                  ],
                  onChanged: (v) => setS(() => estado = v ?? estado),
                ),

                if (saving) ...[
                  const SizedBox(height: 16),
                  const LinearProgressIndicator(),
                ],
              ],
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
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            content: Text('Estudiante, materia y nota final son obligatorios'),
                            backgroundColor: Colors.red,
                          ),
                        );
                        return;
                      }
                      setS(() => saving = true);
                      try {
                        final nueva = Calificacion(
                          calificacionId: cal?.calificacionId,
                          estudianteId: estId!,
                          materiaId: matId!,
                          notaParcial1: double.tryParse(p1Ctrl.text),
                          notaParcial2: double.tryParse(p2Ctrl.text),
                          notaFinal: double.tryParse(fnCtrl.text),
                          semestre: int.tryParse(semCtrl.text),
                          estado: estado,
                        );
                        if (cal != null) {
                          await ApiService.updateCalificacion(cal.calificacionId!, nueva);
                        } else {
                          await ApiService.createCalificacion(nueva);
                        }
                        if (!ctx.mounted) return;
                        Navigator.pop(ctx);
                        if (context.mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                            content: Text(cal == null
                                ? 'Calificación creada ✅'
                                : 'Calificación actualizada ✅'),
                            backgroundColor: Colors.green,
                          ));
                          _load();
                        }
                      } catch (e) {
                        setS(() => saving = false);
                        if (context.mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(content: Text('Error: $e'), backgroundColor: Colors.red),
                          );
                        }
                      }
                    },
              icon: const Icon(Icons.save),
              label: Text(cal == null ? 'Guardar' : 'Actualizar'),
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
        contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 12),
        isDense: true,
      );

  Widget _label(String t) => Padding(
        padding: const EdgeInsets.only(bottom: 4),
        child: Text(
          t,
          style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
        ),
      );

  Widget _numField(
    TextEditingController c,
    String hint, {
    bool isInt = false,
  }) =>
      TextField(
        controller: c,
        keyboardType: TextInputType.numberWithOptions(decimal: !isInt),
        decoration: InputDecoration(
          hintText: hint,
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
          contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 12),
          isDense: true,
        ),
      );

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Calificaciones'),
        backgroundColor: Colors.indigo.shade700,
        foregroundColor: Colors.white,
        elevation: 0,
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _load),
          Padding(
            padding: const EdgeInsets.only(right: 8),
            child: ElevatedButton.icon(
              onPressed: _estudiantes.isEmpty ? null : () => _abrirFormulario(),
              icon: const Icon(Icons.add, size: 18),
              label: const Text('Agregar'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.white,
                foregroundColor: Colors.indigo.shade700,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(10),
                ),
              ),
            ),
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? _errorWidget()
              : Column(
                  children: [
                    // ── Barra de búsqueda + contador ──────────────────────
                    Container(
                      color: Colors.indigo.shade50,
                      padding: const EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 10,
                      ),
                      child: Row(
                        children: [
                          Expanded(
                            child: TextField(
                              decoration: InputDecoration(
                                hintText: 'Buscar por estudiante o materia...',
                                prefixIcon: const Icon(Icons.search, size: 20),
                                filled: true,
                                fillColor: Colors.white,
                                border: OutlineInputBorder(
                                  borderRadius: BorderRadius.circular(10),
                                  borderSide: BorderSide.none,
                                ),
                                contentPadding: const EdgeInsets.symmetric(
                                  vertical: 0,
                                ),
                                isDense: true,
                              ),
                              onChanged: (v) => setState(() => _busqueda = v),
                            ),
                          ),
                          const SizedBox(width: 12),
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 12,
                              vertical: 8,
                            ),
                            decoration: BoxDecoration(
                              color: Colors.indigo.shade700,
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: Text(
                              '${_filtradas.length} registros',
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 13,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),

                    // ── Tabla ─────────────────────────────────────────────
                    Expanded(
                      child: _filtradas.isEmpty
                          ? _emptyWidget()
                          : SingleChildScrollView(
                              scrollDirection: Axis.vertical,
                              child: SingleChildScrollView(
                                scrollDirection: Axis.horizontal,
                                child: DataTable(
                                  headingRowColor: WidgetStateProperty.all(
                                    Colors.indigo.shade700,
                                  ),
                                  headingTextStyle: const TextStyle(
                                    color: Colors.white,
                                    fontWeight: FontWeight.bold,
                                  ),
                                  dataRowMinHeight: 52,
                                  dataRowMaxHeight: 60,
                                  columnSpacing: 20,
                                  columns: const [
                                    DataColumn(label: Text('#')),
                                    DataColumn(label: Text('Estudiante')),
                                    DataColumn(label: Text('Materia')),
                                    DataColumn(
                                      label: Text('Parcial 1'),
                                      numeric: true,
                                    ),
                                    DataColumn(
                                      label: Text('Parcial 2'),
                                      numeric: true,
                                    ),
                                    DataColumn(
                                      label: Text('Nota Final'),
                                      numeric: true,
                                    ),
                                    DataColumn(
                                      label: Text('Semestre'),
                                      numeric: true,
                                    ),
                                    DataColumn(label: Text('Estado')),
                                    DataColumn(label: Text('Acciones')),
                                  ],
                                  rows: _filtradas.asMap().entries.map((entry) {
                                    final i = entry.key;
                                    final c = entry.value;
                                    final colorNota = _colorNota(c.notaFinal);
                                    return DataRow(
                                      color: WidgetStateProperty.resolveWith(
                                        (states) => i.isEven
                                            ? Colors.grey.shade50
                                            : Colors.white,
                                      ),
                                      cells: [
                                        DataCell(
                                          Text(
                                            '${i + 1}',
                                            style: TextStyle(
                                              color: Colors.grey.shade500,
                                              fontSize: 12,
                                            ),
                                          ),
                                        ),
                                        DataCell(
                                          Row(
                                            children: [
                                              CircleAvatar(
                                                radius: 14,
                                                backgroundColor:
                                                    Colors.indigo.shade100,
                                                child: Text(
                                                  _nombreEst(c.estudianteId)
                                                          .isNotEmpty
                                                      ? _nombreEst(
                                                          c.estudianteId,
                                                        )[0].toUpperCase()
                                                      : '?',
                                                  style: TextStyle(
                                                    fontSize: 12,
                                                    color: Colors.indigo.shade700,
                                                    fontWeight: FontWeight.bold,
                                                  ),
                                                ),
                                              ),
                                              const SizedBox(width: 8),
                                              SizedBox(
                                                width: 140,
                                                child: Text(
                                                  _nombreEst(c.estudianteId),
                                                  overflow: TextOverflow.ellipsis,
                                                  style: const TextStyle(
                                                    fontWeight: FontWeight.w500,
                                                  ),
                                                ),
                                              ),
                                            ],
                                          ),
                                        ),
                                        DataCell(
                                          SizedBox(
                                            width: 130,
                                            child: Text(
                                              _nombreMat(c.materiaId),
                                              overflow: TextOverflow.ellipsis,
                                            ),
                                          ),
                                        ),
                                        DataCell(
                                          Text(
                                            c.notaParcial1?.toStringAsFixed(1) ??
                                                '—',
                                            style: TextStyle(
                                              color: _colorNota(c.notaParcial1),
                                            ),
                                          ),
                                        ),
                                        DataCell(
                                          Text(
                                            c.notaParcial2?.toStringAsFixed(1) ??
                                                '—',
                                            style: TextStyle(
                                              color: _colorNota(c.notaParcial2),
                                            ),
                                          ),
                                        ),
                                        DataCell(
                                          Container(
                                            padding: const EdgeInsets.symmetric(
                                              horizontal: 10,
                                              vertical: 4,
                                            ),
                                            decoration: BoxDecoration(
                                              color: colorNota.withValues(
                                                alpha: 0.12,
                                              ),
                                              borderRadius: BorderRadius.circular(
                                                20,
                                              ),
                                              border: Border.all(
                                                color: colorNota.withValues(
                                                  alpha: 0.4,
                                                ),
                                              ),
                                            ),
                                            child: Text(
                                              c.notaFinal?.toStringAsFixed(2) ??
                                                  '—',
                                              style: TextStyle(
                                                color: colorNota,
                                                fontWeight: FontWeight.bold,
                                                fontSize: 13,
                                              ),
                                            ),
                                          ),
                                        ),
                                        DataCell(Text('${c.semestre ?? '—'}')),
                                        DataCell(_estadoBadge(c.estado)),
                                        DataCell(
                                          IconButton(
                                            icon: Icon(
                                              Icons.edit_outlined,
                                              color: Colors.indigo.shade600,
                                              size: 20,
                                            ),
                                            tooltip: 'Editar',
                                            onPressed: () =>
                                                _abrirFormulario(cal: c),
                                          ),
                                        ),
                                      ],
                                    );
                                  }).toList(),
                                ),
                              ),
                            ),
                    ),
                  ],
                ),
    );
  }

  Widget _estadoBadge(String estado) {
    Color c;
    switch (estado) {
      case 'aprobado':
        c = Colors.green;
        break;
      case 'reprobado':
        c = Colors.red;
        break;
      default:
        c = Colors.orange;
    }
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: c.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: c.withValues(alpha: 0.4)),
      ),
      child: Text(
        _estadoLabel(estado),
        style: TextStyle(color: c, fontSize: 11, fontWeight: FontWeight.bold),
      ),
    );
  }

  Widget _errorWidget() => Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.wifi_off, size: 60, color: Colors.red.shade300),
            const SizedBox(height: 12),
            const Text('No se pudo cargar calificaciones'),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              onPressed: _load,
              icon: const Icon(Icons.refresh),
              label: const Text('Reintentar'),
            ),
          ],
        ),
      );

  Widget _emptyWidget() => Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.grade_outlined, size: 64, color: Colors.grey.shade300),
            const SizedBox(height: 12),
            Text(
              _busqueda.isEmpty
                  ? 'No hay calificaciones registradas'
                  : 'No se encontraron resultados para "$_busqueda"',
              style: TextStyle(color: Colors.grey.shade500),
            ),
            if (_busqueda.isEmpty) ...[
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: () => _abrirFormulario(),
                icon: const Icon(Icons.add),
                label: const Text('Agregar primera calificación'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.indigo.shade700,
                  foregroundColor: Colors.white,
                ),
              ),
            ],
          ],
        ),
      );
}