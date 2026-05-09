import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart'; // <-- IMPORTANTE PARA ABRIR NAVEGADOR
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
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: _nombreController,
                decoration: InputDecoration(
                  labelText: 'Nombre',
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _descripcionController,
                maxLines: 3,
                decoration: InputDecoration(
                  labelText: 'Descripción',
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancelar'),
          ),
          ElevatedButton(
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
                scaffoldMessenger.showSnackBar(
                  SnackBar(
                    content: Text(_editingCarrera != null
                        ? 'Carrera actualizada ✅'
                        : 'Carrera creada ✅'),
                    backgroundColor: Colors.green,
                  ),
                );
              } catch (e) {
                scaffoldMessenger.showSnackBar(
                  SnackBar(content: Text('Error: $e'), backgroundColor: Colors.red),
                );
              }
            },
            style: ElevatedButton.styleFrom(backgroundColor: Colors.purple.shade700),
            child: const Text('Guardar', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }

  void _deleteCarrera(int id) async {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Eliminar Carrera'),
        content: const Text('¿Está seguro de que desea eliminar esta carrera?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancelar'),
          ),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(ctx);
              try {
                await ApiService.deleteCarrera(id);
                if (!mounted) return;
                setState(() {
                  _futureCarreras = ApiService.getCarreras();
                });
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Carrera eliminada'), backgroundColor: Colors.orange),
                );
              } catch (e) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text('Error: $e'), backgroundColor: Colors.red),
                );
              }
            },
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            child: const Text('Eliminar', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }

  void _mostrarDetallesYMaterias(Carrera carrera, MaterialColor color) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => _BottomSheetMaterias(carrera: carrera, color: color),
    );
  }

  @override
  Widget build(BuildContext context) {
    final isTablet = MediaQuery.of(context).size.width > 768;
    
    return Scaffold(
      appBar: AppBar(
        title: const Text('Programas Educativos'),
        backgroundColor: Colors.purple.shade700,
        foregroundColor: Colors.white,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => setState(() {
              _futureCarreras = ApiService.getCarreras();
            }),
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
            if (carreras.isEmpty) {
              return const Center(child: Text('No hay carreras registradas'));
            }

            return GridView.builder(
              padding: const EdgeInsets.all(16),
              gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: isTablet ? 3 : 2,
                mainAxisSpacing: 16,
                crossAxisSpacing: 16,
                childAspectRatio: isTablet ? 1.0 : 1.1,
              ),
              itemCount: carreras.length,
              itemBuilder: (context, index) {
                final carrera = carreras[index];
                final colors = [Colors.purple, Colors.indigo, Colors.blue, Colors.teal, Colors.green, Colors.orange];
                final color = colors[index % colors.length];

                return GestureDetector(
                  onTap: () => _mostrarDetallesYMaterias(carrera, color),
                  child: Card(
                    elevation: 4,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: Container(
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(16),
                        gradient: LinearGradient(
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                          colors: [color.shade400, color.shade700],
                        ),
                      ),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Padding(
                            padding: const EdgeInsets.all(16),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Icon(Icons.school_rounded, size: 40, color: Colors.white70),
                                const SizedBox(height: 12),
                                Text(
                                  carrera.nombre ?? 'Sin nombre',
                                  style: const TextStyle(
                                    color: Colors.white,
                                    fontSize: 16,
                                    fontWeight: FontWeight.bold,
                                  ),
                                  maxLines: 2,
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ],
                            ),
                          ),
                          Container(
                            width: double.infinity,
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                            decoration: const BoxDecoration(
                              color: Colors.white24,
                              borderRadius: BorderRadius.vertical(bottom: Radius.circular(16)),
                            ),
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.spaceAround,
                              children: [
                                GestureDetector(
                                  onTap: () => _showDialog(carrera: carrera),
                                  child: const Icon(Icons.edit, color: Colors.white, size: 20),
                                ),
                                GestureDetector(
                                  onTap: () => _deleteCarrera(carrera.carreraId!),
                                  child: const Icon(Icons.delete, color: Colors.white, size: 20),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                );
              },
            );
          }
        },
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _showDialog(),
        backgroundColor: Colors.purple.shade700,
        icon: const Icon(Icons.add),
        label: const Text('Nueva Carrera'),
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

// =========================================================================
// MAPA CURRICULAR POR SEMESTRE CON BOTÓN ELIMINAR Y NAVEGADOR
// =========================================================================
class _BottomSheetMaterias extends StatefulWidget {
  final Carrera carrera;
  final MaterialColor color;

  const _BottomSheetMaterias({required this.carrera, required this.color});

  @override
  State<_BottomSheetMaterias> createState() => _BottomSheetMateriasState();
}

class _BottomSheetMateriasState extends State<_BottomSheetMaterias> {
  late Future<List<Map<String, dynamic>>> _futureMaterias;

  @override
  void initState() {
    super.initState();
    _cargarMaterias();
  }

  void _cargarMaterias() {
    _futureMaterias = ApiService.getMateriasRawByCarrera(widget.carrera.carreraId!);
  }

  Future<void> _eliminarMateria(int id) async {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Eliminar Materia'),
        content: const Text('¿Estás seguro de quitar esta materia del mapa curricular?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancelar')),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            onPressed: () async {
              Navigator.pop(ctx);
              try {
                await ApiService.deleteMateria(id);
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Materia eliminada'), backgroundColor: Colors.orange),
                  );
                }
                setState(() {
                  _cargarMaterias();
                });
              } catch (e) {
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Error: $e'), backgroundColor: Colors.red),
                  );
                }
              }
            },
            child: const Text('Eliminar', style: TextStyle(color: Colors.white)),
          )
        ]
      )
    );
  }

  Future<void> _abrirNavegadorUV() async {
    // Liga general de los mapas curriculares de la UV
    final url = Uri.parse('https://www.uv.mx/planesdeestudio/licenciatura/');
    if (!await launchUrl(url, mode: LaunchMode.externalApplication)) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('No se pudo abrir el navegador')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return DraggableScrollableSheet(
      expand: false,
      initialChildSize: 0.8,
      maxChildSize: 0.95,
      minChildSize: 0.5,
      builder: (_, scrollCtrl) => Column(
        children: [
          Container(
            width: 40,
            height: 5,
            margin: const EdgeInsets.symmetric(vertical: 10),
            decoration: BoxDecoration(
              color: Colors.grey.shade300,
              borderRadius: BorderRadius.circular(10)
            ),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        widget.carrera.nombre ?? '',
                        style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: widget.color.shade800),
                      ),
                      const Text('Mapa Curricular', style: TextStyle(color: Colors.grey, fontSize: 13)),
                    ]
                  )
                ),
                IconButton(
                  icon: const Icon(Icons.close),
                  onPressed: () => Navigator.pop(context),
                ),
              ],
            ),
          ),
          const Divider(),
          Expanded(
            child: FutureBuilder<List<Map<String, dynamic>>>(
              future: _futureMaterias,
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return const Center(child: CircularProgressIndicator());
                } else if (snapshot.hasError) {
                  return Center(child: Text('Error: ${snapshot.error}'));
                } else {
                  final materias = snapshot.data ?? [];
                  if (materias.isEmpty) {
                    return Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.library_books, size: 64, color: Colors.grey.shade300),
                          const SizedBox(height: 16),
                          const Text('No hay materias registradas en este programa.'),
                          const SizedBox(height: 8),
                          const Text('Crea las materias en la sección "Materias" y asígnalas a esta carrera.', 
                            textAlign: TextAlign.center,
                            style: TextStyle(color: Colors.grey, fontSize: 12)),
                        ],
                      ),
                    );
                  }

                  // ── AGRUPAR POR SEMESTRE ──
                  final Map<int, List<Map<String, dynamic>>> porSemestre = {};
                  for (var m in materias) {
                    int sem = m['semestre'] ?? 1;
                    porSemestre.putIfAbsent(sem, () => []).add(m);
                  }
                  final semestres = porSemestre.keys.toList()..sort();

                  return ListView.builder(
                    controller: scrollCtrl,
                    padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                    itemCount: semestres.length,
                    itemBuilder: (ctx, i) {
                      final sem = semestres[i];
                      final listaMat = porSemestre[sem]!;
                      
                      return Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          // Título del Semestre
                          Container(
                            margin: const EdgeInsets.only(top: 16, bottom: 8),
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                            decoration: BoxDecoration(
                              color: widget.color.withValues(alpha: 0.1),
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(color: widget.color.withValues(alpha: 0.3))
                            ),
                            child: Text('Semestre $sem', style: TextStyle(fontWeight: FontWeight.bold, color: widget.color.shade800)),
                          ),
                          // Lista de materias del semestre
                          ...listaMat.map((mat) => Card(
                            margin: const EdgeInsets.only(bottom: 8),
                            elevation: 1,
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                            child: ListTile(
                              leading: CircleAvatar(
                                backgroundColor: widget.color.shade50,
                                child: Icon(Icons.book, size: 18, color: widget.color.shade700),
                              ),
                              title: Text(mat['nombre'] ?? '', style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                              subtitle: Text('Créditos: ${mat['creditos'] ?? 0} | Cód: ${mat['codigo']}', style: const TextStyle(fontSize: 11)),
                              trailing: IconButton(
                                icon: const Icon(Icons.delete_outline, color: Colors.redAccent),
                                onPressed: () => _eliminarMateria(mat['materia_id']),
                                tooltip: 'Eliminar Materia',
                              ),
                            ),
                          )),
                        ],
                      );
                    },
                  );
                }
              },
            ),
          ),
          
          // ── BOTÓN PARA ABRIR LA LIGA DE LA UV EN EL NAVEGADOR ──
          Container(
            padding: const EdgeInsets.all(16),
            decoration: const BoxDecoration(
              color: Colors.white,
              boxShadow: [BoxShadow(color: Colors.black12, blurRadius: 4, offset: Offset(0, -2))]
            ),
            child: SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: _abrirNavegadorUV,
                icon: const Icon(Icons.open_in_browser),
                label: const Text('Consultar Plan de Estudios Oficial (UV)'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: widget.color.shade700,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 14)
                ),
              ),
            ),
          )
        ],
      ),
    );
  }
}