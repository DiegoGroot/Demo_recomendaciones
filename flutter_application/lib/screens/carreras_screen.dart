import 'package:flutter/material.dart';
import '../models/carrera.dart';
import '../services/api_service.dart';

class CarrerasScreen extends StatefulWidget {
  const CarrerasScreen({super.key});

  @override
  State<CarrerasScreen> createState() => _CarrerasScreenState();
}

class _CarrerasScreenState extends State<CarrerasScreen> {
  late Future<List<Carrera>> _futureCarreras;
  final TextEditingController _nombreController = TextEditingController();
  final TextEditingController _descripcionController = TextEditingController();
  Carrera? _editingCarrera;

  @override
  void initState() {
    super.initState();
    _futureCarreras = ApiService.getCarreras();
  }

  void _showDialog({Carrera? carrera}) {
    if (carrera != null) {
      _nombreController.text = carrera.nombre ?? '';
      _descripcionController.text = carrera.descripcion ?? '';
      _editingCarrera = carrera;
    } else {
      _nombreController.clear();
      _descripcionController.clear();
      _editingCarrera = null;
    }

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(carrera != null ? 'Editar Carrera' : 'Nueva Carrera'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: _nombreController,
              decoration: const InputDecoration(labelText: 'Nombre'),
            ),
            TextField(
              controller: _descripcionController,
              decoration: const InputDecoration(labelText: 'Descripción'),
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
                final carrera = Carrera(
                  nombre: _nombreController.text,
                  descripcion: _descripcionController.text,
                );
                if (_editingCarrera != null) {
                  await ApiService.updateCarrera(
                      _editingCarrera!.carreraId!, carrera);
                } else {
                  await ApiService.createCarrera(carrera);
                }
                if (!mounted) return;
                setState(() {
                  _futureCarreras = ApiService.getCarreras();
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

  void _deleteCarrera(int id) async {
    try {
      await ApiService.deleteCarrera(id);
      if (!mounted) return;
      setState(() {
        _futureCarreras = ApiService.getCarreras();
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
        title: const Text('Carreras'),
        actions: [
          FloatingActionButton(
            onPressed: () => _showDialog(),
            child: const Icon(Icons.add),
          ),
        ],
      ),
      body: FutureBuilder<List<Carrera>>(
        future: _futureCarreras,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          } else if (snapshot.hasError) {
            return Center(child: Text('Error: ${snapshot.error}'));
          } else {
            final carreras = snapshot.data ?? [];
            return ListView.builder(
              itemCount: carreras.length,
              itemBuilder: (context, index) {
                final carrera = carreras[index];
                return ListTile(
                  title: Text(carrera.nombre ?? 'Sin nombre'),
                  subtitle: Text(carrera.descripcion ?? ''),
                  trailing: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      IconButton(
                        icon: const Icon(Icons.edit),
                        onPressed: () => _showDialog(carrera: carrera),
                      ),
                      IconButton(
                        icon: const Icon(Icons.delete),
                        onPressed: () => _deleteCarrera(carrera.carreraId!),
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
    _nombreController.dispose();
    _descripcionController.dispose();
    super.dispose();
  }
}
