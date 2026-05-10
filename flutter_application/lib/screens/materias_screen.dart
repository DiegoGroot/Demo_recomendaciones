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
  List<Materia>  _materias = [];
  List<Carrera>  _carreras = [];
  bool   _loading = true;
  String? _error;
  String _search = '';
  int?   _filtroCarrera;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final res = await Future.wait([
        ApiService.getMaterias(),
        ApiService.getCarreras(),
      ]);
      if (!mounted) return;
      setState(() {
        _materias = res[0] as List<Materia>;
        _carreras = res[1] as List<Carrera>;
        _loading  = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() { _error = e.toString(); _loading = false; });
    }
  }

  List<Materia> get _filtradas {
    var lista = _materias;
    if (_filtroCarrera != null) {
      lista = lista.where((m) => m.carreraId == _filtroCarrera).toList();
    }
    if (_search.isNotEmpty) {
      final q = _search.toLowerCase();
      lista = lista.where((m) =>
        m.nombre.toLowerCase().contains(q) ||
        m.codigo.toLowerCase().contains(q)).toList();
    }
    return lista;
  }

  String _nombreCarrera(int? id) {
    if (id == null) return 'Sin carrera';
    try { return _carreras.firstWhere((c) => c.carreraId == id).nombre ?? 'Carrera $id'; }
    catch (_) { return 'Carrera $id'; }
  }

  // ── Formulario crear / editar ────────────────────────────────────────────
  void _showForm([Materia? mat]) {
    final nombreCtrl   = TextEditingController(text: mat?.nombre ?? '');
    final codigoCtrl   = TextEditingController(text: mat?.codigo ?? '');
    final creditosCtrl = TextEditingController(text: mat?.creditos?.toString() ?? '');
    final semestreCtrl = TextEditingController(text: mat?.semestre?.toString() ?? '');
    int? carreraId = mat?.carreraId ?? (_carreras.isNotEmpty ? _carreras.first.carreraId : null);
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
                _field(nombreCtrl,   'Nombre *',  Icons.book),
                const SizedBox(height: 12),
                _field(codigoCtrl,   'Código',    Icons.qr_code),
                const SizedBox(height: 12),
                Row(children: [
                  Expanded(child: _field(creditosCtrl, 'Créditos', Icons.stars,
                      type: TextInputType.number)),
                  const SizedBox(width: 12),
                  Expanded(child: _field(semestreCtrl, 'Semestre', Icons.looks_one,
                      type: TextInputType.number)),
                ]),
                const SizedBox(height: 12),
                DropdownButtonFormField<int>(
                  initialValue: carreraId,
                  decoration: InputDecoration(
                    labelText: 'Programa Educativo *',
                    prefixIcon: const Icon(Icons.school),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                  items: _carreras.map((c) => DropdownMenuItem(
                    value: c.carreraId,
                    child: Text(c.nombre ?? '', overflow: TextOverflow.ellipsis),
                  )).toList(),
                  onChanged: (v) => setS(() => carreraId = v),
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
              onPressed: saving ? null : () async {
                if (nombreCtrl.text.trim().isEmpty || carreraId == null) {
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                    content: Text('Nombre y programa educativo son obligatorios'),
                    backgroundColor: Colors.red));
                  return;
                }
                setS(() => saving = true);
                try {
                  final nueva = Materia(
                    materiaId: mat?.materiaId,
                    nombre: nombreCtrl.text.trim(),
                    codigo: codigoCtrl.text.trim(),
                    // FIX: si el campo está vacío, usa null para que el backend conserve el valor
                    creditos: creditosCtrl.text.trim().isEmpty
                        ? null
                        : int.tryParse(creditosCtrl.text),
                    semestre: semestreCtrl.text.trim().isEmpty
                        ? null
                        : int.tryParse(semestreCtrl.text),
                    carreraId: carreraId!,
                  );
                  if (mat != null) {
                    await ApiService.updateMateria(mat.materiaId!, nueva);
                  } else {
                    await ApiService.createMateria(nueva);
                  }
                  if (!ctx.mounted) return;
                  Navigator.pop(ctx);
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                      content: Text(mat == null ? 'Materia creada ✅' : 'Materia actualizada ✅'),
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
              label: Text(mat == null ? 'Crear' : 'Guardar'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.blue.shade700,
                foregroundColor: Colors.white,
              ),
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
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancelar')),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(ctx);
              try {
                await ApiService.deleteMateria(m.materiaId!);
                if (!mounted) return;
                ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                  content: Text('Materia eliminada'), backgroundColor: Colors.orange));
                _load();
              } catch (e) {
                if (!mounted) return;
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text('Error: $e'), backgroundColor: Colors.red));
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
      {TextInputType type = TextInputType.text}) =>
      TextField(
        controller: c, keyboardType: type,
        decoration: InputDecoration(
          labelText: label,
          prefixIcon: Icon(icon),
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
        actions: [IconButton(icon: const Icon(Icons.refresh), onPressed: _load)],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                  Icon(Icons.wifi_off, size: 64, color: Colors.red.shade300),
                  const SizedBox(height: 12),
                  const Text('No se pudo cargar materias'),
                  const SizedBox(height: 16),
                  ElevatedButton.icon(onPressed: _load,
                    icon: const Icon(Icons.refresh), label: const Text('Reintentar')),
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
                          filled: true, fillColor: Colors.white,
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
                          ..._carreras.map((c) => _filtroChip(c.carreraId, c.nombre ?? '')),
                        ]),
                      ),
                    ]),
                  ),
                  Expanded(
                    child: _filtradas.isEmpty
                        ? Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                            Icon(Icons.book_outlined, size: 64, color: Colors.grey.shade300),
                            const SizedBox(height: 12),
                            Text(_search.isEmpty && _filtroCarrera == null
                                ? 'Sin materias registradas'
                                : 'No hay materias con ese filtro',
                                style: TextStyle(color: Colors.grey.shade500)),
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
        label: Text(label, style: TextStyle(fontSize: 12,
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
    // FIX: mostrar '–' cuando creditos es null, evitar mostrar '0' falso
    final creditosLabel = m.creditos != null ? '${m.creditos}' : '–';
    final tieneCreditos = m.creditos != null;

    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      child: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(14),
          gradient: LinearGradient(
            colors: [Colors.blue.shade50, Colors.white],
            begin: Alignment.topLeft, end: Alignment.bottomRight),
        ),
        child: ListTile(
          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          // FIX overflow: tamaños reducidos y ClipRect para que nunca desborde
          leading: Container(
            width: 56, height: 56,
            decoration: BoxDecoration(
              color: tieneCreditos ? Colors.blue.shade700 : Colors.grey.shade400,
              borderRadius: BorderRadius.circular(12),
            ),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                Text(
                  creditosLabel,
                  style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    // FIX: fuente más pequeña si hay 2+ dígitos para no desbordar
                    fontSize: creditosLabel.length > 1 ? 16 : 20,
                  ),
                  overflow: TextOverflow.clip,
                  maxLines: 1,
                ),
                Text(
                  'créd.',
                  style: TextStyle(
                    color: Colors.white.withValues(alpha: 0.85),
                    fontSize: 9,
                  ),
                  overflow: TextOverflow.clip,
                  maxLines: 1,
                ),
              ]),
            ),
          ),
          title: Text(m.nombre,
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
          subtitle: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('Código: ${m.codigo}',
                style: TextStyle(color: Colors.grey.shade600, fontSize: 12)),
            Row(children: [
              Icon(Icons.school, size: 12, color: Colors.blue.shade400),
              const SizedBox(width: 4),
              Expanded(child: Text(carreraNombre,
                  style: TextStyle(color: Colors.blue.shade600, fontSize: 12),
                  overflow: TextOverflow.ellipsis)),
              if (m.semestre != null) ...[
                const SizedBox(width: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: Colors.indigo.shade50,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.indigo.shade200),
                  ),
                  child: Text('Sem. ${m.semestre}',
                      style: TextStyle(fontSize: 10, color: Colors.indigo.shade700,
                          fontWeight: FontWeight.w600)),
                ),
              ],
            ]),
          ]),
          trailing: PopupMenuButton<String>(
            onSelected: (v) {
              if (v == 'edit') _showForm(m);
              if (v == 'delete') _confirmDelete(m);
            },
            itemBuilder: (_) => [
              const PopupMenuItem(value: 'edit',
                  child: Row(children: [
                    Icon(Icons.edit, color: Colors.blue), SizedBox(width: 8), Text('Editar')])),
              const PopupMenuItem(value: 'delete',
                  child: Row(children: [
                    Icon(Icons.delete, color: Colors.red), SizedBox(width: 8),
                    Text('Eliminar', style: TextStyle(color: Colors.red))])),
            ],
          ),
        ),
      ),
    );
  }
}