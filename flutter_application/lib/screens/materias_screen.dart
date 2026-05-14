import 'package:flutter/material.dart';
import '../models/materia.dart';
import '../models/carrera.dart';
import '../services/api_service.dart';

class MateriasScreen extends StatefulWidget {
  const MateriasScreen({super.key});

  @override
  State<MateriasScreen> createState() => _MateriasScreenState();
}

class _MateriasScreenState extends State<MateriasScreen> {
  List<Materia> _materias = [];
  List<Carrera> _carreras = [];
  bool _loading = true;
  String? _error;
  String _search = '';
  int? _filtroCarrera;

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
      final res = await Future.wait([
        ApiService.getMaterias(),
        ApiService.getCarreras(),
      ]);
      if (!mounted) return;
      setState(() {
        _materias = res[0] as List<Materia>;
        _carreras = res[1] as List<Carrera>;
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

  List<Materia> get _filtradas {
    var lista = _materias;
    if (_filtroCarrera != null) {
      lista = lista.where((m) => m.carreraId == _filtroCarrera).toList();
    }
    if (_search.isNotEmpty) {
      final q = _search.toLowerCase();
      lista = lista.where((m) {
        // Manejo ultra seguro contra nulos
        final n = (m.nombre).toLowerCase();
        final c = (m.codigo).toLowerCase();
        return n.contains(q) || c.contains(q);
      }).toList();
    }
    return lista;
  }

  String _nombreCarrera(int? id) {
    if (id == null) return 'Sin carrera';
    try {
      final c = _carreras.firstWhere((c) => c.carreraId == id);
      return c.nombre ?? 'Carrera $id';
    } catch (_) {
      return 'Carrera $id';
    }
  }

  void _showForm([Materia? mat]) {
    final nombreCtrl = TextEditingController(text: mat?.nombre ?? '');
    final codigoCtrl = TextEditingController(text: mat?.codigo ?? '');
    final creditosCtrl = TextEditingController(text: mat?.creditos.toString() ?? '');
    final semestreCtrl = TextEditingController(text: mat?.semestre.toString() ?? '');
    final contenidoCtrl = TextEditingController(text: mat?.contenido ?? '');

    // FIX DEFINITIVO CONTRA NULOS EN DROPDOWN: 
    // Garantizamos que el valor inicial exista dentro de la lista de carreras.
    int? carreraIdSeleccionada = mat?.carreraId;
    if (carreraIdSeleccionada == null && _carreras.isNotEmpty) {
      carreraIdSeleccionada = _carreras.first.carreraId;
    }
    if (carreraIdSeleccionada != null && !_carreras.any((c) => c.carreraId == carreraIdSeleccionada)) {
      carreraIdSeleccionada = null; // Si el ID existe en la materia pero la carrera fue borrada, lo seteamos a null
    }

    bool saving = false;

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setS) => AlertDialog(
          title: Text(mat == null ? 'Nueva Materia' : 'Editar Materia',
              style: const TextStyle(fontWeight: FontWeight.bold)),
          content: SizedBox(
            width: 420,
            child: SingleChildScrollView(
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                _field(nombreCtrl, 'Nombre *', Icons.book),
                const SizedBox(height: 12),
                _field(codigoCtrl, 'Código', Icons.qr_code),
                const SizedBox(height: 12),
                Row(children: [
                  Expanded(
                      child: _field(creditosCtrl, 'Créditos', Icons.stars,
                          type: TextInputType.number)),
                  const SizedBox(width: 12),
                  Expanded(
                      child: _field(semestreCtrl, 'Semestre', Icons.looks_one,
                          type: TextInputType.number)),
                ]),
                const SizedBox(height: 12),
                // DROPDOWN A PRUEBA DE FALLOS
                DropdownButtonFormField<int?>(
                  initialValue: carreraIdSeleccionada,
                  decoration: InputDecoration(
                    labelText: 'Programa Educativo *',
                    prefixIcon: const Icon(Icons.school),
                    border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12)),
                  ),
                  items: [
                    const DropdownMenuItem<int?>(
                      value: null,
                      child: Text('Selecciona una carrera'),
                    ),
                    ..._carreras.map((c) => DropdownMenuItem<int?>(
                          value: c.carreraId,
                          child: Text(c.nombre ?? 'Sin nombre',
                              overflow: TextOverflow.ellipsis),
                        ))
                  ],
                  onChanged: (v) => setS(() => carreraIdSeleccionada = v),
                ),
                const SizedBox(height: 12),
                _field(contenidoCtrl, 'Contenido / Temario (Syllabus)',
                    Icons.list_alt,
                    maxLines: 3),
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
                      if (nombreCtrl.text.trim().isEmpty || carreraIdSeleccionada == null) {
                        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                            content: Text(
                                'Nombre y programa educativo son obligatorios'),
                            backgroundColor: Colors.red));
                        return;
                      }
                      
                      // Validar que créditos y semestre sean válidos
                      int creditos = int.tryParse(creditosCtrl.text.trim()) ?? 3;
                      int semestre = int.tryParse(semestreCtrl.text.trim()) ?? 1;
                      
                      if (creditos <= 0) {
                        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                            content: Text('Los créditos deben ser mayor a 0'),
                            backgroundColor: Colors.red));
                        return;
                      }
                      if (semestre <= 0) {
                        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                            content: Text('El semestre debe ser mayor a 0'),
                            backgroundColor: Colors.red));
                        return;
                      }
                      
                      setS(() => saving = true);
                      try {
                        final nueva = Materia(
                          materiaId: mat?.materiaId,
                          nombre: nombreCtrl.text.trim(),
                          codigo: codigoCtrl.text.trim(),
                          creditos: creditos,
                          semestre: semestre,
                          carreraId: carreraIdSeleccionada,
                          contenido: contenidoCtrl.text.trim().isEmpty
                              ? null
                              : contenidoCtrl.text.trim(),
                        );
                        if (mat != null && mat.materiaId != null) {
                          await ApiService.updateMateria(
                              mat.materiaId!, nueva);
                        } else {
                          await ApiService.createMateria(nueva);
                        }
                        if (!ctx.mounted) return;
                        Navigator.pop(ctx);
                        if (context.mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                              content: Text(mat == null
                                  ? 'Materia creada ✅'
                                  : 'Materia actualizada ✅'),
                              backgroundColor: Colors.green));
                          _load();
                        }
                      } catch (e) {
                        setS(() => saving = false);
                        if (context.mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                              content: Text('Error: $e'),
                              backgroundColor: Colors.red));
                        }
                      }
                    },
              icon: const Icon(Icons.save),
              label: Text(mat == null ? 'Crear' : 'Guardar'),
              style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.blue.shade700,
                  foregroundColor: Colors.white),
            ),
          ],
        ),
      ),
    );
  }

  void _confirmDelete(Materia m) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Eliminar materia'),
        content: Text('¿Eliminar "${m.nombre}"? No se puede deshacer.'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Cancelar')),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(ctx);
              try {
                if (m.materiaId != null) {
                  await ApiService.deleteMateria(m.materiaId!);
                }
                if (!mounted) return;
                ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                    content: Text('Materia eliminada'),
                    backgroundColor: Colors.orange));
                _load();
              } catch (e) {
                if (!mounted) return;
                ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                    content: Text('Error: $e'),
                    backgroundColor: Colors.red));
              }
            },
            style: ElevatedButton.styleFrom(
                backgroundColor: Colors.red, foregroundColor: Colors.white),
            child: const Text('Eliminar'),
          ),
        ],
      ),
    );
  }

  Widget _field(TextEditingController c, String label, IconData icon,
          {TextInputType type = TextInputType.text, int maxLines = 1}) =>
      TextField(
        controller: c,
        keyboardType: type,
        maxLines: maxLines,
        decoration: InputDecoration(
          labelText: label,
          prefixIcon: maxLines == 1 ? Icon(icon) : null,
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
        ),
      );

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Materias (${_filtradas.length})'),
        backgroundColor: Colors.blue.shade700,
        foregroundColor: Colors.white,
        elevation: 0,
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _load)
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(
                  child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                      Icon(Icons.wifi_off,
                          size: 64, color: Colors.red.shade300),
                      const SizedBox(height: 12),
                      const Text('No se pudo cargar materias'),
                      const SizedBox(height: 16),
                      ElevatedButton.icon(
                          onPressed: _load,
                          icon: const Icon(Icons.refresh),
                          label: const Text('Reintentar')),
                    ]))
              : Column(children: [
                  Container(
                    color: Colors.blue.shade50,
                    padding: const EdgeInsets.all(12),
                    child: Column(children: [
                      TextField(
                        decoration: InputDecoration(
                          hintText: 'Buscar materia o código...',
                          prefixIcon: const Icon(Icons.search),
                          filled: true,
                          fillColor: Colors.white,
                          border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(12),
                              borderSide: BorderSide.none),
                          isDense: true,
                        ),
                        onChanged: (v) => setState(() => _search = v),
                      ),
                      const SizedBox(height: 8),
                      SingleChildScrollView(
                        scrollDirection: Axis.horizontal,
                        child: Row(children: [
                          _filtroChip(null, 'Todas'),
                          ..._carreras.map((c) =>
                              _filtroChip(c.carreraId, c.nombre ?? 'Sin nombre')),
                        ]),
                      ),
                    ]),
                  ),
                  Expanded(
                    child: _filtradas.isEmpty
                        ? Center(
                            child: Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                Icon(Icons.book_outlined,
                                    size: 64, color: Colors.grey.shade300),
                                const SizedBox(height: 12),
                                Text(
                                    _search.isEmpty && _filtroCarrera == null
                                        ? 'Sin materias registradas'
                                        : 'No hay materias con ese filtro',
                                    style: TextStyle(
                                        color: Colors.grey.shade500)),
                                if (_search.isEmpty && _filtroCarrera == null) ...[
                                  const SizedBox(height: 16),
                                  ElevatedButton.icon(
                                    onPressed: () => _showForm(),
                                    icon: const Icon(Icons.add),
                                    label: const Text('Crear primera materia'),
                                    style: ElevatedButton.styleFrom(
                                        backgroundColor: Colors.blue.shade700,
                                        foregroundColor: Colors.white),
                                  ),
                                ],
                              ]))
                        : ListView.builder(
                            padding: const EdgeInsets.all(12),
                            itemCount: _filtradas.length,
                            itemBuilder: (_, i) => _materiaCard(_filtradas[i]),
                          ),
                  ),
                ]),
      floatingActionButton: FloatingActionButton.extended(
        heroTag: 'fab_materias',
        onPressed: () => _showForm(),
        backgroundColor: Colors.blue.shade700,
        icon: const Icon(Icons.add),
        label: const Text('Nueva Materia'),
      ),
    );
  }

  Widget _filtroChip(int? carreraId, String label) {
    final sel = _filtroCarrera == carreraId;
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: FilterChip(
        selected: sel,
        label: Text(label,
            style: TextStyle(
                fontSize: 12,
                color: sel ? Colors.white : Colors.blue.shade700)),
        backgroundColor: Colors.white,
        selectedColor: Colors.blue.shade700,
        checkmarkColor: Colors.white,
        side: BorderSide(color: Colors.blue.shade300),
        onSelected: (_) => setState(() => _filtroCarrera = carreraId),
      ),
    );
  }

  Widget _materiaCard(Materia m) {
    final carreraNombre = _nombreCarrera(m.carreraId);
    final creditosLabel = '${m.creditos}';
    final contenido = (m.contenido ?? '').trim();

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      child: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(14),
          gradient: LinearGradient(
            colors: [Colors.blue.shade50, Colors.white],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        child: Padding(
          padding: const EdgeInsets.fromLTRB(12, 12, 8, 12),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              Container(
                width: 56,
                height: 56,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: Colors.blue.shade700,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Flexible(
                      child: FittedBox(
                        fit: BoxFit.scaleDown,
                        child: Text(
                          creditosLabel,
                          style: TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                            fontSize: creditosLabel.length > 1 ? 17 : 22,
                          ),
                        ),
                      ),
                    ),
                    Text(
                      'créd.',
                      style: TextStyle(
                        color: Colors.white.withValues(alpha: 0.85),
                        fontSize: 9,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      m.nombre,
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 15.5,
                      ),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 3),
                    Text(
                      'Código: ${m.codigo}',
                      style: TextStyle(
                        color: Colors.grey.shade600,
                        fontSize: 12,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 3),
                    Wrap(
                      spacing: 8,
                      runSpacing: 4,
                      crossAxisAlignment: WrapCrossAlignment.center,
                      children: [
                        Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(Icons.school, size: 12, color: Colors.blue.shade400),
                            const SizedBox(width: 4),
                            ConstrainedBox(
                              constraints: const BoxConstraints(maxWidth: 210),
                              child: Text(
                                carreraNombre,
                                style: TextStyle(
                                  color: Colors.blue.shade600,
                                  fontSize: 12,
                                ),
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                          ],
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
                          decoration: BoxDecoration(
                            color: Colors.indigo.shade50,
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(color: Colors.indigo.shade200),
                          ),
                          child: Text(
                            'Sem. ${m.semestre}',
                            style: TextStyle(
                              fontSize: 10,
                              color: Colors.indigo.shade700,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ],
                    ),
                    if (contenido.isNotEmpty) ...[
                      const SizedBox(height: 6),
                      Text(
                        'Syllabus: $contenido',
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          fontSize: 11,
                          color: Colors.grey.shade600,
                          fontStyle: FontStyle.italic,
                          height: 1.2,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              PopupMenuButton<String>(
                padding: EdgeInsets.zero,
                icon: const Icon(Icons.more_vert),
                onSelected: (v) {
                  if (v == 'edit') _showForm(m);
                  if (v == 'delete') _confirmDelete(m);
                },
                itemBuilder: (_) => [
                  const PopupMenuItem(
                    value: 'edit',
                    child: Row(children: [
                      Icon(Icons.edit, color: Colors.blue),
                      SizedBox(width: 8),
                      Text('Editar'),
                    ]),
                  ),
                  const PopupMenuItem(
                    value: 'delete',
                    child: Row(children: [
                      Icon(Icons.delete, color: Colors.red),
                      SizedBox(width: 8),
                      Text('Eliminar', style: TextStyle(color: Colors.red)),
                    ]),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}