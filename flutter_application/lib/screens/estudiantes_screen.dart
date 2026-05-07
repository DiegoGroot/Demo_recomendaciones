import 'package:flutter/material.dart';
import '../models/estudiante.dart';
import '../models/carrera.dart';
import '../models/calificacion.dart';
import '../models/recomendacion.dart';
import '../services/api_service.dart';

class EstudiantesScreen extends StatefulWidget {
  const EstudiantesScreen({super.key});

  @override
  State<EstudiantesScreen> createState() => _EstudiantesScreenState();
}

class _EstudiantesScreenState extends State<EstudiantesScreen> {
  List<Estudiante> _estudiantes = [];
  List<Carrera> _carreras = [];
  bool _loading = true;
  String? _error;
  String _search = '';

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final results = await Future.wait([
        ApiService.getEstudiantes(),
        ApiService.getCarreras(),
      ]);
      if (!mounted) return;
      setState(() {
        _estudiantes = results[0] as List<Estudiante>;
        _carreras    = results[1] as List<Carrera>;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() { _error = e.toString(); _loading = false; });
    }
  }

  List<Estudiante> get _filtered => _search.isEmpty
      ? _estudiantes
      : _estudiantes.where((e) =>
          e.nombre.toLowerCase().contains(_search.toLowerCase()) ||
          e.correo.toLowerCase().contains(_search.toLowerCase())).toList();

  String _carreraNombre(int? id) {
    if (id == null) return 'Sin carrera';
    try { return _carreras.firstWhere((c) => c.carreraId == id).nombre ?? 'Sin nombre'; }
    catch (_) { return 'Carrera $id'; }
  }

  // ── Formulario crear/editar ──────────────────────────────────────────────
  void _showForm([Estudiante? est]) {
    final nombreCtrl      = TextEditingController(text: est?.nombre ?? '');
    final correoCtrl      = TextEditingController(text: est?.correo ?? '');
    final passCtrl        = TextEditingController();
    final pass2Ctrl       = TextEditingController();
    final fechaNacCtrl    = TextEditingController(text: est?.fechaNacimiento ?? '');
    final direccionCtrl   = TextEditingController(text: est?.direccion ?? '');
    final matriculaCtrl   = TextEditingController(text: est?.matricula ?? '');
    final nacionalidadCtrl= TextEditingController(text: est?.nacionalidad ?? '');
    int? carreraId = est?.carreraId ?? (_carreras.isNotEmpty ? _carreras.first.carreraId : null);
    String? sexoVal = est?.sexo;
    String? modalidadVal = est?.modalidad;
    bool saving = false;
    bool showPass = false;
    bool showPass2 = false;

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setS) => AlertDialog(
          title: Text(est == null ? 'Nuevo Estudiante' : 'Editar Estudiante',
              style: const TextStyle(fontWeight: FontWeight.bold)),
          content: SizedBox(
            width: 480,
            child: SingleChildScrollView(
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                _field(nombreCtrl, 'Nombre completo *', Icons.person),
                const SizedBox(height: 12),
                _field(correoCtrl, 'Correo electrónico *', Icons.email,
                    type: TextInputType.emailAddress),
                const SizedBox(height: 12),
                // Contraseña con toggle visibilidad
                TextField(
                  controller: passCtrl,
                  obscureText: !showPass,
                  decoration: InputDecoration(
                    labelText: est == null ? 'Contraseña *' : 'Nueva contraseña (opcional)',
                    prefixIcon: const Icon(Icons.lock),
                    suffixIcon: IconButton(
                      icon: Icon(showPass ? Icons.visibility_off : Icons.visibility),
                      onPressed: () => setS(() => showPass = !showPass),
                    ),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                ),
                const SizedBox(height: 12),
                // Confirmar contraseña
                TextField(
                  controller: pass2Ctrl,
                  obscureText: !showPass2,
                  decoration: InputDecoration(
                    labelText: est == null ? 'Confirmar contraseña *' : 'Confirmar nueva contraseña',
                    prefixIcon: const Icon(Icons.lock_outline),
                    suffixIcon: IconButton(
                      icon: Icon(showPass2 ? Icons.visibility_off : Icons.visibility),
                      onPressed: () => setS(() => showPass2 = !showPass2),
                    ),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<int>(
                  initialValue: carreraId,
                  decoration: InputDecoration(
                    labelText: 'Carrera',
                    prefixIcon: const Icon(Icons.school),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                  items: _carreras.map((c) => DropdownMenuItem(
                    value: c.carreraId, child: Text(c.nombre ?? ''))).toList(),
                  onChanged: (v) => setS(() => carreraId = v),
                ),
                const SizedBox(height: 12),
                _field(fechaNacCtrl, 'Fecha de Nacimiento (YYYY-MM-DD)', Icons.calendar_today),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  initialValue: sexoVal,
                  decoration: InputDecoration(
                    labelText: 'Sexo',
                    prefixIcon: const Icon(Icons.wc),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                  items: ['Masculino', 'Femenino', 'Otro']
                      .map((s) => DropdownMenuItem(value: s, child: Text(s))).toList(),
                  onChanged: (v) => setS(() => sexoVal = v),
                ),
                const SizedBox(height: 12),
                _field(nacionalidadCtrl, 'Nacionalidad', Icons.public),
                const SizedBox(height: 12),
                _field(direccionCtrl, 'Dirección', Icons.location_on, maxLines: 2),
                const SizedBox(height: 12),
                _field(matriculaCtrl, 'Matrícula', Icons.badge),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  initialValue: modalidadVal,
                  decoration: InputDecoration(
                    labelText: 'Modalidad',
                    prefixIcon: const Icon(Icons.class_),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                  items: ['Presencial', 'Virtual', 'Híbrida']
                      .map((m) => DropdownMenuItem(value: m, child: Text(m))).toList(),
                  onChanged: (v) => setS(() => modalidadVal = v),
                ),
                if (saving) ...[const SizedBox(height: 16), const LinearProgressIndicator()],
              ]),
            ),
          ),
          actions: [
            TextButton(onPressed: saving ? null : () => Navigator.pop(ctx),
                child: const Text('Cancelar')),
            ElevatedButton.icon(
              onPressed: saving ? null : () async {
                if (nombreCtrl.text.trim().isEmpty || correoCtrl.text.trim().isEmpty) {
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                    content: Text('Nombre y correo son obligatorios'),
                    backgroundColor: Colors.red));
                  return;
                }
                if (est == null && passCtrl.text.isEmpty) {
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                    content: Text('La contraseña es obligatoria'),
                    backgroundColor: Colors.red));
                  return;
                }
                if (passCtrl.text.isNotEmpty && passCtrl.text != pass2Ctrl.text) {
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                    content: Text('Las contraseñas no coinciden'),
                    backgroundColor: Colors.red));
                  return;
                }
                setS(() => saving = true);
                try {
                  final nuevo = Estudiante(
                    estudianteId: est?.estudianteId,
                    nombre: nombreCtrl.text.trim(),
                    correo: correoCtrl.text.trim(),
                    contrasena: passCtrl.text.isNotEmpty ? passCtrl.text : null,
                    carreraId: carreraId,
                    fechaNacimiento: fechaNacCtrl.text.isNotEmpty ? fechaNacCtrl.text : null,
                    sexo: sexoVal,
                    nacionalidad: nacionalidadCtrl.text.isNotEmpty ? nacionalidadCtrl.text : null,
                    direccion: direccionCtrl.text.isNotEmpty ? direccionCtrl.text : null,
                    matricula: matriculaCtrl.text.isNotEmpty ? matriculaCtrl.text : null,
                    modalidad: modalidadVal,
                  );
                  if (est != null) {
                    await ApiService.updateEstudiante(est.estudianteId!, nuevo);
                  } else {
                    await ApiService.createEstudiante(nuevo);
                  }
                  if (!ctx.mounted) return;
                  Navigator.pop(ctx);
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                      content: Text(est == null ? 'Estudiante creado ✅' : 'Estudiante actualizado ✅'),
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
              label: Text(est == null ? 'Crear' : 'Guardar'),
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

  // ── Ver rendimiento del estudiante ───────────────────────────────────────
  void _showRendimiento(Estudiante est) {
    showDialog(
      context: context,
      builder: (ctx) => _RendimientoDialog(
        estudiante: est,
        carreraNombre: _carreraNombre(est.carreraId),
      ),
    );
  }

  void _confirmDelete(Estudiante e) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Eliminar estudiante'),
        content: Text('¿Eliminar a ${e.nombre}? Esta acción no se puede deshacer.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancelar')),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(ctx);
              try {
                await ApiService.deleteEstudiante(e.estudianteId!);
                if (!mounted) return;
                ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                  content: Text('Estudiante eliminado'), backgroundColor: Colors.orange));
                _load();
              } catch (err) {
                if (!mounted) return;
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text('Error: $err'), backgroundColor: Colors.red));
              }
            },
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            child: const Text('Eliminar', style: TextStyle(color: Colors.white)),
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
          prefixIcon: Icon(icon),
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
        ),
      );

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Estudiantes (${_filtered.length})'),
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
                  Text('Error: $_error'),
                  const SizedBox(height: 16),
                  ElevatedButton.icon(onPressed: _load,
                    icon: const Icon(Icons.refresh), label: const Text('Reintentar')),
                ]))
              : Column(children: [
                  Padding(
                    padding: const EdgeInsets.all(12),
                    child: TextField(
                      decoration: InputDecoration(
                        hintText: 'Buscar por nombre o correo...',
                        prefixIcon: const Icon(Icons.search),
                        filled: true, fillColor: Colors.grey.shade100,
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: BorderSide.none),
                      ),
                      onChanged: (v) => setState(() => _search = v),
                    ),
                  ),
                  Expanded(
                    child: _filtered.isEmpty
                        ? const Center(child: Text('No hay estudiantes registrados'))
                        : ListView.builder(
                            padding: const EdgeInsets.symmetric(horizontal: 12),
                            itemCount: _filtered.length,
                            itemBuilder: (_, i) => _estudianteCard(_filtered[i]),
                          ),
                  ),
                ]),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _showForm(),
        backgroundColor: Colors.blue.shade700,
        icon: const Icon(Icons.person_add),
        label: const Text('Nuevo'),
      ),
    );
  }

  Widget _estudianteCard(Estudiante e) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(children: [
          ListTile(
            contentPadding: EdgeInsets.zero,
            leading: CircleAvatar(
              backgroundColor: Colors.blue.shade700, radius: 24,
              child: Text(e.nombre.isNotEmpty ? e.nombre[0].toUpperCase() : '?',
                  style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 18)),
            ),
            title: Text(e.nombre,
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
            subtitle: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(e.correo, style: TextStyle(color: Colors.grey.shade600, fontSize: 12)),
              Text(_carreraNombre(e.carreraId),
                  style: TextStyle(color: Colors.blue.shade600, fontSize: 12)),
            ]),
            trailing: PopupMenuButton<String>(
              onSelected: (action) {
                if (action == 'rendimiento') _showRendimiento(e);
                if (action == 'edit') _showForm(e);
                if (action == 'delete') _confirmDelete(e);
              },
              itemBuilder: (_) => [
                const PopupMenuItem(value: 'rendimiento',
                    child: Row(children: [
                      Icon(Icons.bar_chart, color: Colors.indigo),
                      SizedBox(width: 8),
                      Text('Ver Rendimiento')])),
                const PopupMenuItem(value: 'edit',
                    child: Row(children: [
                      Icon(Icons.edit), SizedBox(width: 8), Text('Editar')])),
                const PopupMenuItem(value: 'delete',
                    child: Row(children: [
                      Icon(Icons.delete, color: Colors.red),
                      SizedBox(width: 8),
                      Text('Eliminar', style: TextStyle(color: Colors.red))])),
              ],
            ),
          ),
          Divider(color: Colors.grey.shade300),
          Wrap(spacing: 8, runSpacing: 6, children: [
            if (e.matricula != null && e.matricula!.isNotEmpty)
              _chip('Matrícula: ${e.matricula}', Icons.badge, Colors.indigo),
            if (e.sexo != null && e.sexo!.isNotEmpty)
              _chip(e.sexo!, Icons.wc, Colors.pink),
            if (e.modalidad != null && e.modalidad!.isNotEmpty)
              _chip(e.modalidad!, Icons.class_, Colors.green),
            if (e.nacionalidad != null && e.nacionalidad!.isNotEmpty)
              _chip(e.nacionalidad!, Icons.public, Colors.amber),
          ]),
        ]),
      ),
    );
  }

  Widget _chip(String label, IconData icon, MaterialColor color) => Chip(
    label: Text(label, style: TextStyle(fontSize: 11, color: color.shade700)),
    avatar: Icon(icon, size: 14, color: color.shade600),
    backgroundColor: color.shade50,
    side: BorderSide(color: color.shade200),
    padding: EdgeInsets.zero,
  );
}

// ── Dialog de rendimiento del estudiante ────────────────────────────────────
class _RendimientoDialog extends StatefulWidget {
  final Estudiante estudiante;
  final String carreraNombre;
  const _RendimientoDialog({required this.estudiante, required this.carreraNombre});

  @override
  State<_RendimientoDialog> createState() => _RendimientoDialogState();
}

class _RendimientoDialogState extends State<_RendimientoDialog> {
  bool _loading = true;
  List<Calificacion> _cals = [];
  List<Recomendacion> _recs = [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final estId = widget.estudiante.estudianteId!;
      final results = await Future.wait([
        ApiService.getCalificacionesByEstudiante(estId),
        ApiService.getRecomendacionesByEstudiante(estId),
      ]);
      if (!mounted) return;
      setState(() {
        _cals = results[0] as List<Calificacion>;
        _recs = results[1] as List<Recomendacion>;
        _loading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _loading = false);
    }
  }

  double get _promedio {
    final notas = _cals.where((c) => c.notaFinal != null).map((c) => c.notaFinal!).toList();
    if (notas.isEmpty) return 0;
    return notas.reduce((a, b) => a + b) / notas.length;
  }


  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Row(children: [
        CircleAvatar(
          backgroundColor: Colors.indigo.shade100, radius: 20,
          child: Text(widget.estudiante.nombre[0].toUpperCase(),
              style: TextStyle(color: Colors.indigo.shade700, fontWeight: FontWeight.bold)),
        ),
        const SizedBox(width: 12),
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(widget.estudiante.nombre,
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          Text(widget.carreraNombre,
              style: TextStyle(fontSize: 12, color: Colors.grey.shade600,
                  fontWeight: FontWeight.normal)),
        ])),
      ]),
      content: SizedBox(
        width: 480,
        child: _loading
            ? const SizedBox(height: 80, child: Center(child: CircularProgressIndicator()))
            : SingleChildScrollView(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  // ── Programa educativo + promedio ──
                  Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      gradient: LinearGradient(colors: [
                        Colors.indigo.shade700, Colors.indigo.shade500]),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Row(children: [
                      const Icon(Icons.school, color: Colors.white, size: 28),
                      const SizedBox(width: 12),
                      Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        const Text('Programa Educativo',
                            style: TextStyle(color: Colors.white70, fontSize: 11)),
                        Text(widget.carreraNombre,
                            style: const TextStyle(color: Colors.white,
                                fontWeight: FontWeight.bold, fontSize: 15)),
                        if (widget.estudiante.matricula != null)
                          Text('Matrícula: ${widget.estudiante.matricula}',
                              style: const TextStyle(color: Colors.white70, fontSize: 11)),
                      ])),
                      Column(children: [
                        Text(_promedio.toStringAsFixed(1),
                            style: TextStyle(
                                color: _promedio >= 3.5 ? Colors.greenAccent : Colors.orangeAccent,
                                fontSize: 32, fontWeight: FontWeight.bold)),
                        const Text('promedio', style: TextStyle(color: Colors.white70, fontSize: 10)),
                      ]),
                    ]),
                  ),
                  const SizedBox(height: 16),

                  // ── Calificaciones por materia ──
                  Text('Materias (${_cals.length})',
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                  const SizedBox(height: 8),
                  if (_cals.isEmpty)
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: Colors.grey.shade50,
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: Colors.grey.shade200),
                      ),
                      child: const Center(child: Text('Sin calificaciones registradas',
                          style: TextStyle(color: Colors.grey))),
                    )
                  else
                    ..._cals.map((c) {
                      final nota = c.notaFinal;
                      final color = nota == null
                          ? Colors.grey
                          : nota >= 3.5 ? Colors.green.shade700
                          : nota >= 2.5 ? Colors.orange.shade700
                          : Colors.red.shade700;
                      return Container(
                        margin: const EdgeInsets.only(bottom: 8),
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(color: Colors.grey.shade200),
                        ),
                        child: Row(children: [
                          Container(
                            width: 44, height: 44,
                            decoration: BoxDecoration(
                              color: color.withValues(alpha: 0.12),
                              shape: BoxShape.circle,
                              border: Border.all(color: color, width: 2),
                            ),
                            child: Center(child: Text(
                              nota?.toStringAsFixed(1) ?? '-',
                              style: TextStyle(fontWeight: FontWeight.bold,
                                  color: color, fontSize: 13),
                            )),
                          ),
                          const SizedBox(width: 12),
                          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                            Text(c.materiaNombre ?? 'Materia ${c.materiaId}',
                                style: const TextStyle(fontWeight: FontWeight.w600)),
                            Row(children: [
                              _notaChip('P1', c.notaParcial1),
                              const SizedBox(width: 6),
                              _notaChip('P2', c.notaParcial2),
                              const SizedBox(width: 6),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                decoration: BoxDecoration(
                                  color: (c.estado == 'aprobado' ? Colors.green : Colors.red)
                                      .withValues(alpha: 0.1),
                                  borderRadius: BorderRadius.circular(6),
                                ),
                                child: Text(c.estado,
                                    style: TextStyle(
                                        fontSize: 10,
                                        color: c.estado == 'aprobado'
                                            ? Colors.green.shade700
                                            : Colors.red.shade700)),
                              ),
                            ]),
                          ])),
                        ]),
                      );
                    }),

                  const SizedBox(height: 16),
                  // ── Recomendaciones activas ──
                  Text('Recomendaciones activas (${_recs.where((r) => r.estado == 'activa').length})',
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                  const SizedBox(height: 8),
                  if (_recs.where((r) => r.estado == 'activa').isEmpty)
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.green.shade50, borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: Colors.green.shade200),
                      ),
                      child: Row(children: [
                        Icon(Icons.check_circle, color: Colors.green.shade600),
                        const SizedBox(width: 8),
                        const Text('Sin recomendaciones pendientes'),
                      ]),
                    )
                  else
                    ..._recs.where((r) => r.estado == 'activa').map((r) {
                      final prioColor = r.prioridad == 'alta'
                          ? Colors.red : r.prioridad == 'media'
                          ? Colors.orange : Colors.green;
                      return Container(
                        margin: const EdgeInsets.only(bottom: 8),
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: prioColor.withValues(alpha: 0.06),
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(color: prioColor.withValues(alpha: 0.3)),
                        ),
                        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                          Icon(Icons.lightbulb, color: prioColor, size: 18),
                          const SizedBox(width: 8),
                          Expanded(child: Text(r.descripcion,
                              style: const TextStyle(fontSize: 13))),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(
                              color: prioColor.withValues(alpha: 0.15),
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: Text(r.prioridad.toUpperCase(),
                                style: TextStyle(fontSize: 10, color: prioColor,
                                    fontWeight: FontWeight.bold)),
                          ),
                        ]),
                      );
                    }),
                ]),
              ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cerrar')),
      ],
    );
  }

  Widget _notaChip(String label, double? nota) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
    decoration: BoxDecoration(color: Colors.grey.shade100,
        borderRadius: BorderRadius.circular(6)),
    child: Text('$label: ${nota?.toStringAsFixed(1) ?? "-"}',
        style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w500)),
  );
}