import 'package:flutter/material.dart';
import '../services/auth_service.dart';
import '../services/api_service.dart';

class SettingsScreen extends StatefulWidget {
  final VoidCallback onLogout;
  const SettingsScreen({super.key, required this.onLogout});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  bool _notificacionesEnabled = true;
  String _idioma = 'es';

  // ── Estado admins ─────────────────────────────────────────────────────────
  List<Map<String, dynamic>> _admins = [];
  bool _loadingAdmins = false;
  String? _adminsError;
  bool _isSuperAdmin = false; // se calcula después de cargar la lista

  @override
  void initState() {
    super.initState();
    _cargarAdmins();
  }

  Future<void> _cargarAdmins() async {
    setState(() { _loadingAdmins = true; _adminsError = null; });
    try {
      final data = await ApiService.listarAdmins();
      if (!mounted) return;
      final myId = AuthService().userId;
      final myEntry = data.where((a) => a['usuario_id'] == myId).firstOrNull;
      final rolEsAdmin = (myEntry?['rol'] ?? '').toString().toLowerCase() == 'admin';
      setState(() {
        _admins = data;
        _loadingAdmins = false;
        _isSuperAdmin = rolEsAdmin;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() { _adminsError = e.toString(); _loadingAdmins = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    final myId = AuthService().userId;
    final isSuperAdmin = _isSuperAdmin;
    return Scaffold(
      backgroundColor: Colors.grey.shade50,
      appBar: AppBar(
        title: const Text('Configuración'),
        backgroundColor: Colors.indigo.shade700,
        foregroundColor: Colors.white,
        elevation: 0,
      ),
      body: SingleChildScrollView(
        child: Column(
          children: [
            // Cuenta
            _sectionHeader('Cuenta'),
            Card(
              margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text('Usuario: ${AuthService().userEmail}',
                      style: const TextStyle(fontSize: 14)),
                  const SizedBox(height: 8),
                  Text('ID: ${AuthService().userId ?? "N/A"}',
                      style: TextStyle(fontSize: 12, color: Colors.grey.shade600)),
                ]),
              ),
            ),

            // Preferencias
            _sectionHeader('Preferencias'),
            _settingTile(
              title: 'Notificaciones',
              subtitle: 'Recibir notificaciones del sistema',
              trailing: Switch(
                value: _notificacionesEnabled,
                onChanged: (v) => setState(() => _notificacionesEnabled = v),
              ),
            ),
            _settingTile(
              title: 'Idioma',
              subtitle: 'Seleccionar idioma de la aplicación',
              trailing: DropdownButton<String>(
                value: _idioma,
                items: const [
                  DropdownMenuItem(value: 'es', child: Text('Español')),
                  DropdownMenuItem(value: 'en', child: Text('English')),
                ],
                onChanged: (v) => setState(() => _idioma = v ?? 'es'),
              ),
            ),

            // Información
            _sectionHeader('Información'),
            _infoTile(
              icon: Icons.info_outline, title: 'Versión de la App',
              subtitle: '1.0.0', color: Colors.blue,
            ),
            _infoTile(
              icon: Icons.description_outlined, title: 'Términos y Condiciones',
              subtitle: 'Ver términos de uso', color: Colors.purple,
              onTap: () => _mostrarDialog('Términos y Condiciones',
                'Esta aplicación SIRA está diseñada para mejorar el desempeño académico '
                'de los estudiantes mediante recomendaciones personalizadas basadas en su rendimiento.'),
            ),
            _infoTile(
              icon: Icons.privacy_tip_outlined, title: 'Política de Privacidad',
              subtitle: 'Ver política de privacidad', color: Colors.green,
              onTap: () => _mostrarDialog('Política de Privacidad',
                'Tus datos personales se utilizan únicamente para proporcionar un mejor '
                'servicio educativo. No compartimos información con terceros.'),
            ),

            // Administradores
            _sectionHeader('Administradores'),
            _adminsSection(myId, isSuperAdmin: isSuperAdmin),

            // Acciones
            _sectionHeader('Acciones'),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: _confirmarCerrarSesion,
                  icon: const Icon(Icons.logout),
                  label: const Text('Cerrar Sesión'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.red.shade600,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 12),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }

  // ── Sección Administradores ───────────────────────────────────────────────
  Widget _adminsSection(int? myId, {bool isSuperAdmin = false}) {
    if (_loadingAdmins) {
      return const Padding(
        padding: EdgeInsets.symmetric(vertical: 24),
        child: Center(child: CircularProgressIndicator()),
      );
    }
    if (_adminsError != null) {
      return Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        child: Card(
          color: Colors.red.shade50,
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Row(children: [
              Icon(Icons.error_outline, color: Colors.red.shade400),
              const SizedBox(width: 8),
              Expanded(child: Text('Error al cargar admins',
                  style: TextStyle(color: Colors.red.shade700))),
              TextButton(onPressed: _cargarAdmins, child: const Text('Reintentar')),
            ]),
          ),
        ),
      );
    }
    return Column(children: [
      Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        child: Row(children: [
          Icon(Icons.admin_panel_settings, size: 16, color: Colors.indigo.shade400),
          const SizedBox(width: 6),
          Text('${_admins.length} administrador(es) registrado(s)',
              style: TextStyle(fontSize: 12, color: Colors.grey.shade600)),
          const Spacer(),
          IconButton(
            icon: const Icon(Icons.refresh, size: 18),
            onPressed: _cargarAdmins,
            tooltip: 'Recargar',
            color: Colors.indigo.shade400,
            constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
          ),
        ]),
      ),
      ..._admins.map((admin) {
        final isMe = admin['usuario_id'] == myId;
        return _adminCard(admin, isMe, isSuperAdmin: isSuperAdmin);
      }),
    ]);
  }

  Widget _adminCard(Map<String, dynamic> admin, bool isMe, {bool isSuperAdmin = false}) {
    final nombre = admin['nombre'] ?? 'Sin nombre';
    final correo = admin['correo'] ?? '';
    final rol    = admin['rol'] ?? 'admin';
    final estado = admin['estado'] ?? 'activo';

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      elevation: isMe ? 2 : 1,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(10),
        side: isMe
            ? BorderSide(color: Colors.indigo.shade300, width: 1.5)
            : BorderSide.none,
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        child: Row(children: [
          CircleAvatar(
            radius: 22,
            backgroundColor: isMe ? Colors.indigo.shade100 : Colors.grey.shade200,
            child: Text(
              nombre.isNotEmpty ? nombre[0].toUpperCase() : '?',
              style: TextStyle(
                fontWeight: FontWeight.bold,
                color: isMe ? Colors.indigo.shade700 : Colors.grey.shade600,
              ),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                Flexible(
                  child: Text(nombre,
                      style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
                      overflow: TextOverflow.ellipsis),
                ),
                if (isMe) ...[
                  const SizedBox(width: 6),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: Colors.indigo.shade100,
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text('Tú', style: TextStyle(
                        fontSize: 10, color: Colors.indigo.shade700,
                        fontWeight: FontWeight.bold)),
                  ),
                ],
              ]),
              Text(correo,
                  style: TextStyle(fontSize: 12, color: Colors.grey.shade500),
                  overflow: TextOverflow.ellipsis),
              const SizedBox(height: 2),
              Row(children: [
                _badge(rol, Colors.indigo),
                const SizedBox(width: 6),
                _badge(estado, estado == 'activo' ? Colors.green : Colors.orange),
              ]),
            ]),
          ),
          if (!isMe && isSuperAdmin)
            PopupMenuButton<String>(
              icon: Icon(Icons.more_vert, color: Colors.grey.shade500),
              onSelected: (action) => _handleAdminAction(action, admin),
              itemBuilder: (_) => [
                const PopupMenuItem(value: 'editar', child: Row(children: [
                  Icon(Icons.edit, size: 18, color: Colors.indigo),
                  SizedBox(width: 10), Text('Modificar usuario'),
                ])),
                const PopupMenuItem(value: 'contrasena', child: Row(children: [
                  Icon(Icons.lock_reset, size: 18, color: Colors.orange),
                  SizedBox(width: 10), Text('Cambiar contraseña'),
                ])),
                const PopupMenuDivider(),
                const PopupMenuItem(value: 'eliminar', child: Row(children: [
                  Icon(Icons.delete_outline, size: 18, color: Colors.red),
                  SizedBox(width: 10),
                  Text('Eliminar cuenta', style: TextStyle(color: Colors.red)),
                ])),
              ],
            ),
        ]),
      ),
    );
  }

  void _handleAdminAction(String action, Map<String, dynamic> admin) {
    switch (action) {
      case 'editar':     _dialogEditarAdmin(admin);      break;
      case 'contrasena': _dialogCambiarContrasena(admin); break;
      case 'eliminar':   _confirmarEliminarAdmin(admin);  break;
    }
  }

  // ── Dialog: Editar admin ──────────────────────────────────────────────────
  void _dialogEditarAdmin(Map<String, dynamic> admin) {
    final nombreCtrl = TextEditingController(text: admin['nombre'] ?? '');
    final correoCtrl = TextEditingController(text: admin['correo'] ?? '');
    bool saving = false;

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setS) => AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
          title: Row(children: [
            Icon(Icons.edit, color: Colors.indigo.shade600),
            const SizedBox(width: 8),
            const Text('Modificar administrador'),
          ]),
          content: Column(mainAxisSize: MainAxisSize.min, children: [
            TextField(controller: nombreCtrl,
                decoration: _inputDeco('Nombre completo', Icons.person)),
            const SizedBox(height: 12),
            TextField(controller: correoCtrl,
                keyboardType: TextInputType.emailAddress,
                decoration: _inputDeco('Correo electrónico', Icons.email)),
            if (saving) ...[const SizedBox(height: 12), const LinearProgressIndicator()],
          ]),
          actions: [
            TextButton(
              onPressed: saving ? null : () {
                nombreCtrl.dispose(); correoCtrl.dispose();
                Navigator.pop(ctx);
              },
              child: const Text('Cancelar'),
            ),
            ElevatedButton.icon(
              onPressed: saving ? null : () async {
                final nombre = nombreCtrl.text.trim();
                final correo = correoCtrl.text.trim();
                if (nombre.isEmpty && correo.isEmpty) return;
                setS(() => saving = true);
                try {
                  await ApiService.actualizarAdmin(
                    admin['usuario_id'] as int,
                    nombre: nombre.isEmpty ? null : nombre,
                    correo: correo.isEmpty ? null : correo,
                    ejecutorId: AuthService().userId ?? 0,
                  );
                  nombreCtrl.dispose(); correoCtrl.dispose();
                  if (!ctx.mounted) return;
                  Navigator.pop(ctx);
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                      content: Text('Administrador actualizado ✅'),
                      backgroundColor: Colors.green,
                    ));
                    _cargarAdmins();
                  }
                } catch (e) {
                  setS(() => saving = false);
                  if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Error: $e'), backgroundColor: Colors.red));
                }
              },
              icon: const Icon(Icons.save),
              label: const Text('Guardar'),
              style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.indigo.shade700, foregroundColor: Colors.white),
            ),
          ],
        ),
      ),
    );
  }

  // ── Dialog: Cambiar contraseña ────────────────────────────────────────────
  void _dialogCambiarContrasena(Map<String, dynamic> admin) {
    final passCtrl    = TextEditingController();
    final confirmCtrl = TextEditingController();
    bool saving   = false;
    bool showPass = false;

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setS) => AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
          title: Row(children: [
            Icon(Icons.lock_reset, color: Colors.orange.shade600),
            const SizedBox(width: 8),
            const Text('Cambiar contraseña'),
          ]),
          content: Column(mainAxisSize: MainAxisSize.min, children: [
            Text('Admin: ${admin['nombre'] ?? admin['correo']}',
                style: TextStyle(fontSize: 13, color: Colors.grey.shade600)),
            const SizedBox(height: 14),
            TextField(
              controller: passCtrl,
              obscureText: !showPass,
              decoration: _inputDeco('Nueva contraseña', Icons.lock_outline).copyWith(
                suffixIcon: IconButton(
                  icon: Icon(showPass ? Icons.visibility_off : Icons.visibility),
                  onPressed: () => setS(() => showPass = !showPass),
                ),
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: confirmCtrl,
              obscureText: !showPass,
              decoration: _inputDeco('Confirmar contraseña', Icons.lock),
            ),
            if (saving) ...[const SizedBox(height: 12), const LinearProgressIndicator()],
          ]),
          actions: [
            TextButton(
              onPressed: saving ? null : () {
                passCtrl.dispose(); confirmCtrl.dispose();
                Navigator.pop(ctx);
              },
              child: const Text('Cancelar'),
            ),
            ElevatedButton.icon(
              onPressed: saving ? null : () async {
                final pass    = passCtrl.text.trim();
                final confirm = confirmCtrl.text.trim();
                if (pass.isEmpty) {
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                      content: Text('Escribe la nueva contraseña')));
                  return;
                }
                if (pass != confirm) {
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                    content: Text('Las contraseñas no coinciden'),
                    backgroundColor: Colors.red));
                  return;
                }
                if (pass.length < 4) {
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                    content: Text('Mínimo 4 caracteres'),
                    backgroundColor: Colors.red));
                  return;
                }
                setS(() => saving = true);
                try {
                  await ApiService.cambiarContrasenaAdmin(
                      admin['usuario_id'] as int, pass,
                      ejecutorId: AuthService().userId ?? 0);
                  passCtrl.dispose(); confirmCtrl.dispose();
                  if (!ctx.mounted) return;
                  Navigator.pop(ctx);
                  if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Contraseña actualizada ✅'),
                        backgroundColor: Colors.green));
                } catch (e) {
                  setS(() => saving = false);
                  if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Error: $e'), backgroundColor: Colors.red));
                }
              },
              icon: const Icon(Icons.check),
              label: const Text('Cambiar'),
              style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.orange.shade700, foregroundColor: Colors.white),
            ),
          ],
        ),
      ),
    );
  }

  // ── Dialog: Confirmar eliminar ────────────────────────────────────────────
  void _confirmarEliminarAdmin(Map<String, dynamic> admin) {
    bool deleting = false;

    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setS) => AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
          title: Row(children: [
            Icon(Icons.warning_amber_rounded, color: Colors.red.shade600, size: 26),
            const SizedBox(width: 8),
            const Text('¿Eliminar cuenta?'),
          ]),
          content: Column(mainAxisSize: MainAxisSize.min, children: [
            Text('¿Estás seguro de que deseas eliminar la cuenta de:',
                style: TextStyle(color: Colors.grey.shade700)),
            const SizedBox(height: 10),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: Colors.red.shade50,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.red.shade200),
              ),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(admin['nombre'] ?? '',
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                Text(admin['correo'] ?? '',
                    style: TextStyle(fontSize: 12, color: Colors.grey.shade600)),
              ]),
            ),
            const SizedBox(height: 10),
            Text('Esta acción no se puede deshacer.',
                style: TextStyle(fontSize: 12, color: Colors.red.shade600,
                    fontWeight: FontWeight.w500)),
            if (deleting) ...[const SizedBox(height: 12), const LinearProgressIndicator()],
          ]),
          actions: [
            TextButton(
              onPressed: deleting ? null : () => Navigator.pop(ctx),
              child: const Text('Cancelar'),
            ),
            ElevatedButton.icon(
              onPressed: deleting ? null : () async {
                setS(() => deleting = true);
                try {
                  await ApiService.eliminarAdmin(admin['usuario_id'] as int,
                      ejecutorId: AuthService().userId ?? 0);
                  if (!ctx.mounted) return;
                  Navigator.pop(ctx);
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                      content: Text('Cuenta de ${admin['nombre']} eliminada'),
                      backgroundColor: Colors.orange,
                    ));
                    _cargarAdmins();
                  }
                } catch (e) {
                  setS(() => deleting = false);
                  if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Error: $e'), backgroundColor: Colors.red));
                }
              },
              icon: const Icon(Icons.delete_forever),
              label: const Text('Sí, eliminar'),
              style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.red.shade600, foregroundColor: Colors.white),
            ),
          ],
        ),
      ),
    );
  }

  // ── Helpers ───────────────────────────────────────────────────────────────
  Widget _sectionHeader(String title) => Padding(
        padding: const EdgeInsets.fromLTRB(16, 20, 16, 8),
        child: Align(
          alignment: Alignment.centerLeft,
          child: Text(title, style: TextStyle(
              fontSize: 14, fontWeight: FontWeight.bold,
              color: Colors.indigo.shade700)),
        ),
      );

  Widget _settingTile({required String title, required String subtitle,
      required Widget trailing}) =>
      Card(
        margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        child: ListTile(
          title: Text(title, style: const TextStyle(fontWeight: FontWeight.w500)),
          subtitle: Text(subtitle, style: TextStyle(color: Colors.grey.shade600)),
          trailing: trailing,
        ),
      );

  Widget _infoTile({required IconData icon, required String title,
      required String subtitle, required Color color, VoidCallback? onTap}) =>
      Card(
        margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        child: ListTile(
          leading: Icon(icon, color: color),
          title: Text(title, style: const TextStyle(fontWeight: FontWeight.w500)),
          subtitle: Text(subtitle),
          trailing: const Icon(Icons.chevron_right),
          onTap: onTap,
        ),
      );

  Widget _badge(String text, MaterialColor color) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
        decoration: BoxDecoration(
          color: color.shade50,
          borderRadius: BorderRadius.circular(6),
          border: Border.all(color: color.shade200),
        ),
        child: Text(text, style: TextStyle(fontSize: 10,
            color: color.shade700, fontWeight: FontWeight.w600)),
      );

  InputDecoration _inputDeco(String hint, IconData icon) => InputDecoration(
        hintText: hint,
        prefixIcon: Icon(icon, size: 18),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
        enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(10),
            borderSide: BorderSide(color: Colors.grey.shade300)),
        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      );

  void _mostrarDialog(String title, String content) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(title),
        content: SingleChildScrollView(child: Text(content)),
        actions: [TextButton(onPressed: () => Navigator.pop(ctx),
            child: const Text('Entendido'))],
      ),
    );
  }

  void _confirmarCerrarSesion() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('¿Cerrar sesión?'),
        content: const Text('¿Estás seguro de que deseas cerrar sesión?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancelar')),
          ElevatedButton(
            onPressed: () { Navigator.pop(ctx); widget.onLogout(); },
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            child: const Text('Cerrar sesión', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }
}