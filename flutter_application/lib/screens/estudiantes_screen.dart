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

  static const List<String> _nacionalidadesBase = [
    'Mexicano',
    'Estadounidense',
    'Canadiense',
    'Colombiano',
    'Venezolano',
    'Argentino',
    'Chileno',
    'Peruano',
    'Ecuatoriano',
    'Guatemalteco',
    'Hondureño',
    'Salvadoreño',
    'Español',
    'Francés',
    'Italiano',
    'Alemán',
    'Otro',
  ];

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
      final results = await Future.wait([
        ApiService.getEstudiantes(),
        ApiService.getCarreras(),
      ]);
      if (!mounted) return;
      setState(() {
        _estudiantes = results[0] as List<Estudiante>;
        _carreras = results[1] as List<Carrera>;
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

  List<Estudiante> get _filtered {
    if (_search.trim().isEmpty) return _estudiantes;
    final q = _search.toLowerCase().trim();
    return _estudiantes.where((e) {
      final nacionalidad = (e.nacionalidad ?? '').toLowerCase();
      final matricula = (e.matricula ?? '').toLowerCase();
      final carrera = _carreraNombre(e.carreraId).toLowerCase();
      return e.nombre.toLowerCase().contains(q) ||
          e.correo.toLowerCase().contains(q) ||
          nacionalidad.contains(q) ||
          matricula.contains(q) ||
          carrera.contains(q);
    }).toList();
  }

  String _carreraNombre(int? id) {
    if (id == null) return 'Sin carrera';
    try {
      return _carreras.firstWhere((c) => c.carreraId == id).nombre ?? 'Sin nombre';
    } catch (_) {
      return 'Carrera $id';
    }
  }

  List<String> _parseNacionalidades(String? value) {
    if (value == null || value.trim().isEmpty) return [];
    return value
        .split(',')
        .map((n) => n.trim())
        .where((n) => n.isNotEmpty)
        .toSet()
        .toList();
  }

  String _joinNacionalidades(List<String> nacionalidades) {
    return nacionalidades
        .map((n) => n.trim())
        .where((n) => n.isNotEmpty)
        .toSet()
        .join(', ');
  }

  void _showForm([Estudiante? est]) {
    final nombreCtrl = TextEditingController(text: est?.nombre ?? '');
    final correoCtrl = TextEditingController(text: est?.correo ?? '');
    final passCtrl = TextEditingController();
    final pass2Ctrl = TextEditingController();
    final fechaNacCtrl = TextEditingController(text: est?.fechaNacimiento ?? '');
    final direccionCtrl = TextEditingController(text: est?.direccion ?? '');
    final matriculaCtrl = TextEditingController(text: est?.matricula ?? '');
    final nacionalidadOtraCtrl = TextEditingController();

    int? carreraId = est?.carreraId ?? (_carreras.isNotEmpty ? _carreras.first.carreraId : null);
    String? sexoVal = est?.sexo;
    String? modalidadVal = est?.modalidad;
    int? semestreVal = est?.semestreActual ?? 1;
    List<String> nacionalidadesSeleccionadas = _parseNacionalidades(est?.nacionalidad);

    bool saving = false;
    bool showPass = false;
    bool showPass2 = false;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setS) {
          return Container(
            constraints: BoxConstraints(
              maxHeight: MediaQuery.of(ctx).size.height * 0.92,
              maxWidth: 720,
            ),
            margin: EdgeInsets.only(
              left: 12,
              right: 12,
              bottom: MediaQuery.of(ctx).viewInsets.bottom + 12,
              top: 12,
            ),
            decoration: BoxDecoration(
              color: Theme.of(ctx).dialogBackgroundColor,
              borderRadius: BorderRadius.circular(24),
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const SizedBox(height: 10),
                Container(
                  width: 52,
                  height: 5,
                  decoration: BoxDecoration(
                    color: Colors.grey.shade300,
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.fromLTRB(20, 18, 20, 8),
                  child: Row(
                    children: [
                      Icon(est == null ? Icons.person_add : Icons.edit, color: Colors.blue.shade700),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          est == null ? 'Nuevo Estudiante' : 'Editar Estudiante',
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 22),
                        ),
                      ),
                    ],
                  ),
                ),
                Flexible(
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.fromLTRB(20, 8, 20, 12),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        _sectionTitle('Datos principales'),
                        _field(nombreCtrl, 'Nombre completo *', Icons.person),
                        const SizedBox(height: 12),
                        _field(correoCtrl, 'Correo electrónico *', Icons.email, type: TextInputType.emailAddress),
                        const SizedBox(height: 12),
                        TextField(
                          controller: passCtrl,
                          obscureText: !showPass,
                          decoration: _deco(
                            est == null ? 'Contraseña *' : 'Nueva contraseña (opcional)',
                            Icons.lock,
                            suffix: IconButton(
                              icon: Icon(showPass ? Icons.visibility_off : Icons.visibility),
                              onPressed: () => setS(() => showPass = !showPass),
                            ),
                          ),
                        ),
                        const SizedBox(height: 12),
                        TextField(
                          controller: pass2Ctrl,
                          obscureText: !showPass2,
                          decoration: _deco(
                            est == null ? 'Confirmar contraseña *' : 'Confirmar nueva contraseña',
                            Icons.lock_outline,
                            suffix: IconButton(
                              icon: Icon(showPass2 ? Icons.visibility_off : Icons.visibility),
                              onPressed: () => setS(() => showPass2 = !showPass2),
                            ),
                          ),
                        ),
                        const SizedBox(height: 18),
                        _sectionTitle('Información académica'),
                        DropdownButtonFormField<int>(
                          value: carreraId,
                          isExpanded: true,
                          decoration: _deco('Programa Educativo', Icons.school),
                          items: _carreras
                              .map((c) => DropdownMenuItem(value: c.carreraId, child: Text(c.nombre ?? '')))
                              .toList(),
                          onChanged: (v) => setS(() => carreraId = v),
                        ),
                        const SizedBox(height: 12),
                        DropdownButtonFormField<int>(
                          value: semestreVal,
                          decoration: _deco('Semestre Actual', Icons.looks_one),
                          items: List.generate(
                            12,
                            (index) => DropdownMenuItem(value: index + 1, child: Text('${index + 1}° Semestre')),
                          ),
                          onChanged: (v) => setS(() => semestreVal = v),
                        ),
                        const SizedBox(height: 12),
                        _field(matriculaCtrl, 'Matrícula', Icons.badge),
                        const SizedBox(height: 12),
                        DropdownButtonFormField<String>(
                          value: modalidadVal,
                          isExpanded: true,
                          decoration: _deco('Modalidad', Icons.class_),
                          items: ['Presencial', 'Virtual', 'Híbrida']
                              .map((m) => DropdownMenuItem(value: m, child: Text(m)))
                              .toList(),
                          onChanged: (v) => setS(() => modalidadVal = v),
                        ),
                        const SizedBox(height: 18),
                        _sectionTitle('Información personal'),
                        TextField(
                          controller: fechaNacCtrl,
                          readOnly: true,
                          onTap: () async {
                            FocusScope.of(context).requestFocus(FocusNode());
                            final initial = DateTime.tryParse(fechaNacCtrl.text) ?? DateTime(2005);
                            final date = await showDatePicker(
                              context: context,
                              initialDate: initial,
                              firstDate: DateTime(1950),
                              lastDate: DateTime.now(),
                            );
                            if (date != null) {
                              setS(() => fechaNacCtrl.text = date.toString().substring(0, 10));
                            }
                          },
                          decoration: _deco('Fecha de Nacimiento', Icons.calendar_today),
                        ),
                        const SizedBox(height: 12),
                        DropdownButtonFormField<String>(
                          value: sexoVal,
                          isExpanded: true,
                          decoration: _deco('Sexo', Icons.wc),
                          items: ['Masculino', 'Femenino', 'Otro', 'Prefiero no decirlo']
                              .map((s) => DropdownMenuItem(value: s, child: Text(s)))
                              .toList(),
                          onChanged: (v) => setS(() => sexoVal = v),
                        ),
                        const SizedBox(height: 12),
                        _nacionalidadesSelector(
                          nacionalidadesSeleccionadas,
                          nacionalidadOtraCtrl,
                          setS,
                        ),
                        const SizedBox(height: 12),
                        _field(direccionCtrl, 'Dirección', Icons.location_on, maxLines: 2),
                        if (saving) ...[
                          const SizedBox(height: 18),
                          const LinearProgressIndicator(),
                        ],
                      ],
                    ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.fromLTRB(20, 10, 20, 16),
                  decoration: BoxDecoration(
                    border: Border(top: BorderSide(color: Colors.grey.shade200)),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.end,
                    children: [
                      TextButton(
                        onPressed: saving ? null : () => Navigator.pop(ctx),
                        child: const Text('Cancelar'),
                      ),
                      const SizedBox(width: 10),
                      ElevatedButton.icon(
                        onPressed: saving
                            ? null
                            : () async {
                                if (nombreCtrl.text.trim().isEmpty || correoCtrl.text.trim().isEmpty) {
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(
                                      content: Text('Nombre y correo son obligatorios'),
                                      backgroundColor: Colors.red,
                                    ),
                                  );
                                  return;
                                }
                                if (est == null && passCtrl.text.trim().isEmpty) {
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(content: Text('La contraseña es obligatoria'), backgroundColor: Colors.red),
                                  );
                                  return;
                                }
                                if (passCtrl.text.trim().isNotEmpty && passCtrl.text.trim() != pass2Ctrl.text.trim()) {
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(content: Text('Las contraseñas no coinciden'), backgroundColor: Colors.red),
                                  );
                                  return;
                                }
                                setS(() => saving = true);
                                try {
                                  final nacionalidadTexto = _joinNacionalidades(nacionalidadesSeleccionadas);
                                  final nuevo = Estudiante(
                                    estudianteId: est?.estudianteId,
                                    nombre: nombreCtrl.text.trim(),
                                    correo: correoCtrl.text.trim(),
                                    contrasena: passCtrl.text.trim().isNotEmpty ? passCtrl.text.trim() : null,
                                    carreraId: carreraId,
                                    fechaNacimiento: fechaNacCtrl.text.trim().isNotEmpty ? fechaNacCtrl.text.trim() : null,
                                    sexo: sexoVal,
                                    nacionalidad: nacionalidadTexto.isNotEmpty ? nacionalidadTexto : null,
                                    direccion: direccionCtrl.text.trim().isNotEmpty ? direccionCtrl.text.trim() : null,
                                    matricula: matriculaCtrl.text.trim().isNotEmpty ? matriculaCtrl.text.trim() : null,
                                    modalidad: modalidadVal,
                                    semestreActual: semestreVal,
                                  );
                                  if (est != null) {
                                    await ApiService.updateEstudiante(est.estudianteId!, nuevo);
                                  } else {
                                    await ApiService.createEstudiante(nuevo);
                                  }

                                  if (!ctx.mounted) return;
                                  Navigator.pop(ctx);
                                  if (context.mounted) {
                                    ScaffoldMessenger.of(context).showSnackBar(
                                      SnackBar(
                                        content: Text(est == null ? 'Estudiante creado ✅' : 'Estudiante actualizado ✅'),
                                        backgroundColor: Colors.green,
                                      ),
                                    );
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
                        label: Text(est == null ? 'Crear' : 'Guardar'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.blue.shade700,
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _nacionalidadesSelector(
    List<String> seleccionadas,
    TextEditingController otraCtrl,
    StateSetter setS,
  ) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        border: Border.all(color: Colors.grey.shade500),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.public, size: 20),
              const SizedBox(width: 10),
              const Expanded(
                child: Text('Nacionalidad(es)', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w500)),
              ),
              if (seleccionadas.length > 1)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.indigo.shade50,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: Colors.indigo.shade100),
                  ),
                  child: Text(
                    '${seleccionadas.length} nacionalidades',
                    style: TextStyle(color: Colors.indigo.shade700, fontSize: 11, fontWeight: FontWeight.bold),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 10),
          Wrap(
            spacing: 8,
            runSpacing: 6,
            children: _nacionalidadesBase.map((n) {
              final selected = seleccionadas.contains(n);
              return FilterChip(
                label: Text(n),
                selected: selected,
                onSelected: (v) {
                  setS(() {
                    if (v) {
                      if (!seleccionadas.contains(n)) seleccionadas.add(n);
                    } else {
                      seleccionadas.remove(n);
                    }
                  });
                },
                selectedColor: Colors.blue.shade100,
                checkmarkColor: Colors.blue.shade700,
              );
            }).toList(),
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: otraCtrl,
                  decoration: InputDecoration(
                    labelText: 'Agregar otra nacionalidad',
                    hintText: 'Ej. Brasileño',
                    isDense: true,
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              ElevatedButton(
                onPressed: () {
                  final nueva = otraCtrl.text.trim();
                  if (nueva.isEmpty) return;
                  setS(() {
                    if (!seleccionadas.contains(nueva)) seleccionadas.add(nueva);
                    otraCtrl.clear();
                  });
                },
                child: const Text('Agregar'),
              ),
            ],
          ),
          if (seleccionadas.isNotEmpty) ...[
            const SizedBox(height: 10),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: seleccionadas
                  .map(
                    (n) => Chip(
                      label: Text(n),
                      avatar: const Icon(Icons.flag, size: 16),
                      onDeleted: () => setS(() => seleccionadas.remove(n)),
                      backgroundColor: Colors.green.shade50,
                      side: BorderSide(color: Colors.green.shade100),
                    ),
                  )
                  .toList(),
            ),
          ],
          const SizedBox(height: 4),
          Text(
            'Puedes seleccionar una o varias nacionalidades. Se guardan separadas por coma.',
            style: TextStyle(color: Colors.grey.shade600, fontSize: 11),
          ),
        ],
      ),
    );
  }

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
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Estudiante eliminado'), backgroundColor: Colors.orange),
                );
                _load();
              } catch (err) {
                if (!mounted) return;
                ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $err'), backgroundColor: Colors.red));
              }
            },
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            child: const Text('Eliminar', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }

  Widget _field(
    TextEditingController c,
    String label,
    IconData icon, {
    TextInputType type = TextInputType.text,
    int maxLines = 1,
  }) {
    return TextField(
      controller: c,
      keyboardType: type,
      maxLines: maxLines,
      decoration: _deco(label, icon),
    );
  }

  InputDecoration _deco(String label, IconData icon, {Widget? suffix}) {
    return InputDecoration(
      labelText: label,
      prefixIcon: Icon(icon),
      suffixIcon: suffix,
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide(color: Colors.grey.shade500),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide(color: Colors.blue.shade700, width: 2),
      ),
    );
  }

  Widget _sectionTitle(String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Text(
        text,
        style: TextStyle(fontWeight: FontWeight.bold, color: Colors.blue.shade800, fontSize: 14),
      ),
    );
  }

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
              ? Center(child: Text('Error: $_error'))
              : Column(
                  children: [
                    Padding(
                      padding: const EdgeInsets.all(12),
                      child: TextField(
                        decoration: InputDecoration(
                          hintText: 'Buscar por nombre, correo, matrícula, carrera o nacionalidad...',
                          prefixIcon: const Icon(Icons.search),
                          border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                        ),
                        onChanged: (v) => setState(() => _search = v),
                      ),
                    ),
                    Expanded(
                      child: _filtered.isEmpty
                          ? const Center(child: Text('No hay estudiantes'))
                          : ListView.builder(
                              padding: const EdgeInsets.symmetric(horizontal: 12),
                              itemCount: _filtered.length,
                              itemBuilder: (_, i) => _estudianteCard(_filtered[i]),
                            ),
                    ),
                  ],
                ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _showForm(),
        backgroundColor: Colors.blue.shade700,
        icon: const Icon(Icons.person_add),
        label: const Text('Nuevo'),
      ),
    );
  }

  Widget _estudianteCard(Estudiante e) {
    final nacionalidades = _parseNacionalidades(e.nacionalidad);
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          children: [
            ListTile(
              contentPadding: EdgeInsets.zero,
              leading: CircleAvatar(
                backgroundColor: Colors.blue.shade700,
                radius: 24,
                child: Text(
                  e.nombre.isNotEmpty ? e.nombre[0].toUpperCase() : '?',
                  style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                ),
              ),
              title: Text(e.nombre, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
              subtitle: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(e.correo),
                  Text(_carreraNombre(e.carreraId), style: TextStyle(color: Colors.blue.shade600)),
                  if (nacionalidades.isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.only(top: 4),
                      child: Text(
                        nacionalidades.length > 1
                            ? 'Nacionalidades: ${nacionalidades.join(', ')}'
                            : 'Nacionalidad: ${nacionalidades.first}',
                        style: TextStyle(color: Colors.grey.shade700, fontSize: 12),
                      ),
                    ),
                ],
              ),
              trailing: PopupMenuButton<String>(
                onSelected: (a) {
                  if (a == 'rendimiento') _showRendimiento(e);
                  if (a == 'edit') _showForm(e);
                  if (a == 'delete') _confirmDelete(e);
                },
                itemBuilder: (_) => const [
                  PopupMenuItem(
                    value: 'rendimiento',
                    child: Row(children: [Icon(Icons.bar_chart, color: Colors.indigo), SizedBox(width: 8), Text('Ver Rendimiento')]),
                  ),
                  PopupMenuItem(value: 'edit', child: Row(children: [Icon(Icons.edit), SizedBox(width: 8), Text('Editar')])),
                  PopupMenuItem(
                    value: 'delete',
                    child: Row(children: [Icon(Icons.delete, color: Colors.red), SizedBox(width: 8), Text('Eliminar', style: TextStyle(color: Colors.red))]),
                  ),
                ],
              ),
            ),
            Divider(color: Colors.grey.shade300),
            Wrap(
              spacing: 8,
              runSpacing: 6,
              children: [
                if (e.matricula != null && e.matricula!.isNotEmpty) _chip('Matrícula: ${e.matricula}', Icons.badge, Colors.indigo),
                if (e.semestreActual != null) _chip('Semestre ${e.semestreActual}', Icons.looks_one, Colors.blue),
                if (e.sexo != null && e.sexo!.isNotEmpty) _chip(e.sexo!, Icons.wc, Colors.pink),
                if (e.modalidad != null && e.modalidad!.isNotEmpty) _chip(e.modalidad!, Icons.class_, Colors.green),
                if (nacionalidades.length > 1) _chip('${nacionalidades.length} nacionalidades', Icons.public, Colors.purple),
                if (nacionalidades.length == 1) _chip(nacionalidades.first, Icons.public, Colors.purple),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _chip(String label, IconData icon, MaterialColor color) {
    return Chip(
      label: Text(label, style: TextStyle(fontSize: 11, color: color.shade700)),
      avatar: Icon(icon, size: 14, color: color.shade600),
      backgroundColor: color.shade50,
      side: BorderSide(color: color.shade200),
      padding: EdgeInsets.zero,
    );
  }
}

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

  List<String> _parseNacionalidades(String? value) {
    if (value == null || value.trim().isEmpty) return [];
    return value.split(',').map((n) => n.trim()).where((n) => n.isNotEmpty).toList();
  }

  @override
  Widget build(BuildContext context) {
    final nacionalidades = _parseNacionalidades(widget.estudiante.nacionalidad);
    return AlertDialog(
      title: Row(
        children: [
          CircleAvatar(
            backgroundColor: Colors.indigo.shade100,
            radius: 20,
            child: Text(
              widget.estudiante.nombre[0].toUpperCase(),
              style: TextStyle(color: Colors.indigo.shade700, fontWeight: FontWeight.bold),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(widget.estudiante.nombre, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                Text(widget.carreraNombre, style: TextStyle(fontSize: 12, color: Colors.grey.shade600)),
              ],
            ),
          ),
        ],
      ),
      content: SizedBox(
        width: 520,
        child: _loading
            ? const SizedBox(height: 80, child: Center(child: CircularProgressIndicator()))
            : SingleChildScrollView(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        gradient: LinearGradient(colors: [Colors.indigo.shade700, Colors.indigo.shade500]),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.school, color: Colors.white, size: 28),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text('Programa Educativo', style: TextStyle(color: Colors.white70, fontSize: 11)),
                                Text(widget.carreraNombre, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 15)),
                                if (widget.estudiante.matricula != null && widget.estudiante.matricula!.isNotEmpty)
                                  Text('Matrícula: ${widget.estudiante.matricula}', style: const TextStyle(color: Colors.white70, fontSize: 11)),
                                if (nacionalidades.isNotEmpty)
                                  Text('Nacionalidad(es): ${nacionalidades.join(', ')}', style: const TextStyle(color: Colors.white70, fontSize: 11)),
                              ],
                            ),
                          ),
                          Column(
                            children: [
                              Text(
                                _promedio.toStringAsFixed(1),
                                style: TextStyle(
                                  color: _promedio >= 6.0 ? Colors.greenAccent : Colors.orangeAccent,
                                  fontSize: 32,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              const Text('promedio', style: TextStyle(color: Colors.white70, fontSize: 10)),
                            ],
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),
                    Text('Materias (${_cals.length})', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                    const SizedBox(height: 8),
                    if (_cals.isEmpty)
                      const Center(child: Text('Sin calificaciones registradas', style: TextStyle(color: Colors.grey)))
                    else
                      ..._cals.map((c) {
                        final nota = c.notaFinal;
                        final color = nota == null
                            ? Colors.grey
                            : nota >= 8.0
                                ? Colors.green.shade700
                                : nota >= 6.0
                                    ? Colors.orange.shade700
                                    : Colors.red.shade700;
                        return Container(
                          margin: const EdgeInsets.only(bottom: 8),
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(10),
                            border: Border.all(color: Colors.grey.shade200),
                          ),
                          child: Row(
                            children: [
                              Container(
                                width: 44,
                                height: 44,
                                decoration: BoxDecoration(
                                  color: color.withOpacity(0.12),
                                  shape: BoxShape.circle,
                                  border: Border.all(color: color, width: 2),
                                ),
                                child: Center(
                                  child: Text(
                                    nota?.toStringAsFixed(1) ?? '-',
                                    style: TextStyle(fontWeight: FontWeight.bold, color: color, fontSize: 13),
                                  ),
                                ),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(c.materiaNombre ?? 'Materia', style: const TextStyle(fontWeight: FontWeight.w600)),
                                    Wrap(
                                      spacing: 6,
                                      children: [
                                        _notaChip('P1', c.notaParcial1),
                                        _notaChip('P2', c.notaParcial2),
                                        if (c.notaParcial3 != null) _notaChip('P3', c.notaParcial3),
                                      ],
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        );
                      }),
                    const SizedBox(height: 16),
                    Text(
                      'Recomendaciones activas (${_recs.where((r) => r.estado == 'activa').length})',
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                    ),
                    const SizedBox(height: 8),
                    if (_recs.where((r) => r.estado == 'activa').isEmpty)
                      const Text('Sin recomendaciones pendientes')
                    else
                      ..._recs.where((r) => r.estado == 'activa').map((r) {
                        final prioColor = r.prioridad == 'alta'
                            ? Colors.red
                            : r.prioridad == 'media'
                                ? Colors.orange
                                : Colors.green;
                        return Container(
                          margin: const EdgeInsets.only(bottom: 8),
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: prioColor.withOpacity(0.06),
                            borderRadius: BorderRadius.circular(10),
                            border: Border.all(color: prioColor.withOpacity(0.3)),
                          ),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Icon(Icons.lightbulb, color: prioColor, size: 18),
                              const SizedBox(width: 8),
                              Expanded(child: Text(r.descripcion, style: const TextStyle(fontSize: 13))),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                decoration: BoxDecoration(
                                  color: prioColor.withOpacity(0.15),
                                  borderRadius: BorderRadius.circular(6),
                                ),
                                child: Text(
                                  r.prioridad.toUpperCase(),
                                  style: TextStyle(fontSize: 10, color: prioColor, fontWeight: FontWeight.bold),
                                ),
                              ),
                            ],
                          ),
                        );
                      }),
                  ],
                ),
              ),
      ),
      actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cerrar'))],
    );
  }

  Widget _notaChip(String label, double? nota) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(color: Colors.grey.shade100, borderRadius: BorderRadius.circular(6)),
      child: Text('$label: ${nota?.toStringAsFixed(1) ?? "-"}', style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w500)),
    );
  }
}