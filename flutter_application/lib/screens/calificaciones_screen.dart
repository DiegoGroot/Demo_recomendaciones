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
  late Future<List<Calificacion>> _futureCalificaciones;
  late Future<List<Estudiante>> _futureEstudiantes;
  late Future<List<Materia>> _futureMaterias;
  final TextEditingController _calificacionController = TextEditingController();
  final TextEditingController _periodoController = TextEditingController();
  int? _selectedEstudianteId;
  int? _selectedMateriaId;
  Calificacion? _editingCalificacion;

  @override
  void initState() {
    super.initState();
    _futureCalificaciones = ApiService.getCalificaciones();
    _futureEstudiantes = ApiService.getEstudiantes();
    _futureMaterias = ApiService.getMaterias();
    _periodoController.text = '2024-1';
  }

  void _showDialog({Calificacion? calificacion}) {
    if (calificacion != null) {
      _calificacionController.text = calificacion.notaFinal?.toString() ?? '';
      _periodoController.text = 'Semestre ${calificacion.semestre}';
      _selectedEstudianteId = calificacion.estudianteId;
      _selectedMateriaId = calificacion.materiaId;
      _editingCalificacion = calificacion;
    } else {
      _calificacionController.clear();
      _periodoController.text = '2024-1';
      _selectedEstudianteId = null;
      _selectedMateriaId = null;
      _editingCalificacion = null;
    }

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(calificacion != null ? 'Editar Calificación' : 'Nueva Calificación'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            FutureBuilder<List<Estudiante>>(
              future: _futureEstudiantes,
              builder: (context, snapshot) {
                if (snapshot.hasData) {
                  return DropdownButton<int>(
                    hint: const Text('Selecciona estudiante'),
                    value: _selectedEstudianteId,
                    items: snapshot.data!
                        .map((e) => DropdownMenuItem(
                              value: e.estudianteId,
                              child: Text(e.nombre),
                            ))
                        .toList(),
                    onChanged: (value) {
                      setState(() {
                        _selectedEstudianteId = value;
                      });
                    },
                  );
                }
                return const CircularProgressIndicator();
              },
            ),
            FutureBuilder<List<Materia>>(
              future: _futureMaterias,
              builder: (context, snapshot) {
                if (snapshot.hasData) {
                  return DropdownButton<int>(
                    hint: const Text('Selecciona materia'),
                    value: _selectedMateriaId,
                    items: snapshot.data!
                        .map((m) => DropdownMenuItem(
                              value: m.materiaId,
                              child: Text(m.nombre),
                            ))
                        .toList(),
                    onChanged: (value) {
                      setState(() {
                        _selectedMateriaId = value;
                      });
                    },
                  );
                }
                return const CircularProgressIndicator();
              },
            ),
            TextField(
              controller: _calificacionController,
              decoration: const InputDecoration(labelText: 'Calificación'),
              keyboardType: TextInputType.number,
            ),
            TextField(
              controller: _periodoController,
              decoration: const InputDecoration(labelText: 'Período'),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancelar'),
          ),
          TextButton(
            onPressed: () async {
              final navigator = Navigator.of(context);
              final scaffoldMessenger = ScaffoldMessenger.of(context);
              try {
                final calificacion = Calificacion(
                  estudianteId: _selectedEstudianteId!,
                  materiaId: _selectedMateriaId!,
                  notaFinal: double.parse(_calificacionController.text),
                  semestre: int.tryParse(_periodoController.text.replaceAll(RegExp(r'\D'), '')) ?? 1,
                );
                if (_editingCalificacion != null) {
                  await ApiService.updateCalificacion(_editingCalificacion!.calificacionId!, calificacion);
                } else {
                  await ApiService.createCalificacion(calificacion);
                }
                if (!mounted) return;
                setState(() {
                  _futureCalificaciones = ApiService.getCalificaciones();
                });
                navigator.pop();
              } catch (e) {
                if (!mounted) return;
                scaffoldMessenger.showSnackBar(
                  SnackBar(content: Text('Error: $e')),
                );
              }
            },
            child: const Text('Guardar'),
          ),
        ],
      ),
    );
  }

  void _deleteCalificacion(int id) async {
    try {
      await ApiService.deleteCalificacion(id);
      if (!mounted) return;
      setState(() {
        _futureCalificaciones = ApiService.getCalificaciones();
      });
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Calificaciones'),
        actions: [
          FloatingActionButton(
            onPressed: () => _showDialog(),
            child: const Icon(Icons.add),
          ),
        ],
      ),
      body: FutureBuilder<List<Calificacion>>(
        future: _futureCalificaciones,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          } else if (snapshot.hasError) {
            return Center(child: Text('Error: ${snapshot.error}'));
          } else {
            final calificaciones = snapshot.data ?? [];
            return ListView.builder(
              itemCount: calificaciones.length,
              itemBuilder: (context, index) {
                final calificacion = calificaciones[index];
                return ListTile(
                  title: Text('Estudiante ${calificacion.estudianteId} - Materia ${calificacion.materiaId}'),
                  subtitle: Text('Nota Final: ${calificacion.notaFinal ?? 'N/A'}, Semestre: ${calificacion.semestre}'),
                  trailing: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      IconButton(
                        icon: const Icon(Icons.edit),
                        onPressed: () => _showDialog(calificacion: calificacion),
                      ),
                      IconButton(
                        icon: const Icon(Icons.delete),
                        onPressed: () => _deleteCalificacion(calificacion.calificacionId!),
                      ),
                    ],
                  ),
                );
              },
            );
          }
        },
      ),
    );
  }

  @override
  void dispose() {
    _calificacionController.dispose();
    _periodoController.dispose();
    super.dispose();
  }
}
