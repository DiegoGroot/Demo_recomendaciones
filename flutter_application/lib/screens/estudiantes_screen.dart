import 'package:flutter/material.dart';
import '../models/estudiante.dart';
import '../models/carrera.dart';
import '../services/api_service.dart';
import 'recomendaciones_screen.dart';

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

  List<Estudiante> get _filtered => _search.isEmpty
      ? _estudiantes
      : _estudiantes
          .where((e) =>
              e.nombre.toLowerCase().contains(_search.toLowerCase()) ||
              e.correo.toLowerCase().contains(_search.toLowerCase()))
          .toList();

  String _carreraNombre(int? id) {
    if (id == null) return 'Sin carrera';
    try {
      return _carreras.firstWhere((c) => c.carreraId == id).nombre ??
          'Sin nombre';
    } catch (_) {
      return 'Carrera $id';
    }
  }

  void _showForm([Estudiante? est]) {
    final nombreCtrl = TextEditingController(text: est?.nombre ?? '');
    final correoCtrl = TextEditingController(text: est?.correo ?? '');
    final passCtrl = TextEditingController();
    int? carreraId = est?.carreraId ??
        (_carreras.isNotEmpty ? _carreras.first.carreraId : null);
    bool saving = false;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (ctx) => StatefulBuilder(
          builder: (ctx, setS) => Padding(
                padding: EdgeInsets.only(
                  bottom: MediaQuery.of(ctx).viewInsets.bottom + 16,
                  left: 16,
                  right: 16,
                  top: 20,
                ),
                child: SingleChildScrollView(
                    child: Column(mainAxisSize: MainAxisSize.min, children: [
                  Text(est == null ? 'Nuevo Estudiante' : 'Editar Estudiante',
                      style: const TextStyle(
                          fontSize: 20, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 20),
                  TextField(
                    controller: nombreCtrl,
                    decoration: InputDecoration(
                        labelText: 'Nombre completo *',
                        border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12)),
                        prefixIcon: const Icon(Icons.person)),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: correoCtrl,
                    keyboardType: TextInputType.emailAddress,
                    decoration: InputDecoration(
                        labelText: 'Correo electrónico *',
                        border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12)),
                        prefixIcon: const Icon(Icons.email)),
                  ),
                  const SizedBox(height: 12),
                  if (est == null)
                    TextField(
                      controller: passCtrl,
                      obscureText: true,
                      decoration: InputDecoration(
                          labelText: 'Contraseña *',
                          border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(12)),
                          prefixIcon: const Icon(Icons.lock)),
                    ),
                  if (est == null) const SizedBox(height: 12),
                  DropdownButtonFormField<int>(
                    initialValue: carreraId,
                    decoration: InputDecoration(
                        labelText: 'Carrera',
                        border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12)),
                        prefixIcon: const Icon(Icons.school)),
                    items: _carreras
                        .map((c) => DropdownMenuItem(
                            value: c.carreraId, child: Text(c.nombre ?? '')))
                        .toList(),
                    onChanged: (v) => carreraId = v,
                  ),
                  const SizedBox(height: 20),
                  Row(children: [
                    Expanded(
                        child: OutlinedButton(
                      onPressed: () => Navigator.pop(ctx),
                      style: OutlinedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(vertical: 14),
                          shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12))),
                      child: const Text('Cancelar'),
                    )),
                    const SizedBox(width: 12),
                    Expanded(
                        child: ElevatedButton(
                      onPressed: saving
                          ? null
                          : () async {
                              if (nombreCtrl.text.trim().isEmpty ||
                                  correoCtrl.text.trim().isEmpty) {
                                ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(
                                        content: Text(
                                            'Nombre y correo son obligatorios'),
                                        backgroundColor: Colors.red));
                                return;
                              }
                              if (est == null && passCtrl.text.trim().isEmpty) {
                                ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(
                                        content: Text(
                                            'La contraseña es obligatoria'),
                                        backgroundColor: Colors.red));
                                return;
                              }
                              setS(() => saving = true);
                              try {
                                final nuevo = Estudiante(
                                  estudianteId: est?.estudianteId,
                                  nombre: nombreCtrl.text.trim(),
                                  correo: correoCtrl.text.trim(),
                                  contrasena: est == null
                                      ? passCtrl.text.trim()
                                      : (est.contrasena ?? ''),
                                  carreraId: carreraId,
                                );
                                if (est != null) {
                                  await ApiService.updateEstudiante(
                                      est.estudianteId!, nuevo);
                                } else {
                                  await ApiService.createEstudiante(nuevo);
                                }
                                if (!mounted) return;
                                if (ctx.mounted) {
                                  Navigator.pop(ctx);
                                }
                                if (context.mounted) {
                                  ScaffoldMessenger.of(context)
                                      .showSnackBar(SnackBar(
                                    content: Text(est == null
                                        ? 'Estudiante creado ✅'
                                        : 'Estudiante actualizado ✅'),
                                    backgroundColor: Colors.green,
                                  ));
                                }
                                _load();
                              } catch (e) {
                                setS(() => saving = false);
                                ScaffoldMessenger.of(context).showSnackBar(
                                    SnackBar(
                                        content: Text('Error: $e'),
                                        backgroundColor: Colors.red));
                              }
                            },
                      style: ElevatedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        backgroundColor: Colors.blue.shade700,
                        shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12)),
                      ),
                      child: saving
                          ? const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(
                                  strokeWidth: 2, color: Colors.white))
                          : Text(est == null ? 'Crear' : 'Guardar',
                              style: const TextStyle(
                                  color: Colors.white, fontSize: 16)),
                    )),
                  ]),
                  const SizedBox(height: 8),
                ])),
              )),
    );
  }

  void _confirmDelete(Estudiante est) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Eliminar Estudiante'),
        content: Text(
            '¿Eliminar a ${est.nombre}? Esta acción no se puede deshacer.'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Cancelar')),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(ctx);
              try {
                await ApiService.deleteEstudiante(est.estudianteId!);
                if (!mounted) return;
                ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                    content: Text('Estudiante eliminado'),
                    backgroundColor: Colors.orange));
                _load();
              } catch (e) {
                if (!mounted) return;
                ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                    content: Text('Error: $e'), backgroundColor: Colors.red));
              }
            },
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            child:
                const Text('Eliminar', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Estudiantes'),
        backgroundColor: Colors.blue.shade700,
        foregroundColor: Colors.white,
        elevation: 0,
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _load),
        ],
      ),
      body: Column(children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
          child: TextField(
            decoration: InputDecoration(
              hintText: 'Buscar por nombre o correo...',
              prefixIcon: const Icon(Icons.search),
              border:
                  OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
              filled: true,
              fillColor: Colors.grey.shade50,
              contentPadding: const EdgeInsets.symmetric(vertical: 0),
            ),
            onChanged: (v) => setState(() => _search = v),
          ),
        ),
        Expanded(child: _buildBody()),
      ]),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _showForm(),
        backgroundColor: Colors.blue.shade700,
        icon: const Icon(Icons.person_add),
        label: const Text('Nuevo', style: TextStyle(color: Colors.white)),
      ),
    );
  }

  Widget _buildBody() {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return Center(
          child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
        Icon(Icons.wifi_off, size: 64, color: Colors.red.shade300),
        const SizedBox(height: 12),
        const Text('No se pudo conectar con la API'),
        const SizedBox(height: 16),
        ElevatedButton.icon(
            onPressed: _load,
            icon: const Icon(Icons.refresh),
            label: const Text('Reintentar')),
      ]));
    }

    final lista = _filtered;
    if (lista.isEmpty) {
      return Center(
          child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
        Icon(Icons.school, size: 64, color: Colors.grey.shade400),
        const SizedBox(height: 12),
        Text(_search.isEmpty
            ? 'No hay estudiantes registrados'
            : 'Sin resultados para "$_search"'),
      ]));
    }

    return ListView.builder(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 80),
      itemCount: lista.length,
      itemBuilder: (ctx, i) {
        final e = lista[i];
        return Card(
          margin: const EdgeInsets.only(bottom: 10),
          elevation: 2,
          shape:
              RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          child: ListTile(
            contentPadding:
                const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            leading: CircleAvatar(
              backgroundColor: Colors.blue.shade700,
              child: Text(e.nombre[0].toUpperCase(),
                  style: const TextStyle(
                      color: Colors.white, fontWeight: FontWeight.bold)),
            ),
            title: Text(e.nombre,
                style: const TextStyle(fontWeight: FontWeight.bold)),
            subtitle:
                Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(e.correo,
                  style: TextStyle(color: Colors.grey.shade600, fontSize: 12)),
              Text(_carreraNombre(e.carreraId),
                  style: TextStyle(color: Colors.blue.shade600, fontSize: 12)),
            ]),
            trailing: PopupMenuButton<String>(
              onSelected: (action) {
                if (action == 'edit') _showForm(e);
                if (action == 'delete') _confirmDelete(e);
                if (action == 'recs') {
                  Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => RecomendacionesScreen(estudiante: e),
                      ));
                }
              },
              itemBuilder: (_) => [
                const PopupMenuItem(
                    value: 'recs',
                    child: Row(children: [
                      Icon(Icons.lightbulb, color: Colors.purple),
                      SizedBox(width: 8),
                      Text('Ver Recomendaciones')
                    ])),
                const PopupMenuItem(
                    value: 'edit',
                    child: Row(children: [
                      Icon(Icons.edit),
                      SizedBox(width: 8),
                      Text('Editar')
                    ])),
                const PopupMenuItem(
                    value: 'delete',
                    child: Row(children: [
                      Icon(Icons.delete, color: Colors.red),
                      SizedBox(width: 8),
                      Text('Eliminar', style: TextStyle(color: Colors.red))
                    ])),
              ],
            ),
          ),
        );
      },
    );
  }
}
