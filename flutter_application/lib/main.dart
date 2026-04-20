import 'package:flutter/material.dart';
import 'screens/login_screen.dart';
import 'screens/admin_dashboard_screen.dart';
import 'screens/estudiante_home_screen.dart';
import 'screens/carreras_screen.dart';
import 'screens/materias_screen.dart';
import 'screens/estudiantes_screen.dart';
import 'screens/calificaciones_screen.dart';
import 'screens/recomendaciones_screen.dart';
import 'services/auth_service.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SIRA',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue.shade700),
        useMaterial3: true,
      ),
      home: const AuthWrapper(),
    );
  }
}

class AuthWrapper extends StatefulWidget {
  const AuthWrapper({super.key});
  @override
  State<AuthWrapper> createState() => _AuthWrapperState();
}

class _AuthWrapperState extends State<AuthWrapper> {
  bool _isLoggedIn = false;
  void _onLogin(bool ok) => setState(() => _isLoggedIn = ok);
  void _onLogout() {
    AuthService.logout();
    setState(() => _isLoggedIn = false);
  }

  @override
  Widget build(BuildContext context) {
    if (!_isLoggedIn) return LoginScreen(onLoginSuccess: _onLogin);
    if (AuthService.isAdmin) return AdminHomePage(onLogout: _onLogout);
    return EstudianteHomeScreen(onLogout: _onLogout);
  }
}

// ── Página principal del ADMIN con nav bar completo ─────────────────────────
class AdminHomePage extends StatefulWidget {
  final VoidCallback onLogout;
  const AdminHomePage({super.key, required this.onLogout});
  @override
  State<AdminHomePage> createState() => _AdminHomePageState();
}

class _AdminHomePageState extends State<AdminHomePage> {
  int _idx = 0;

  late final List<Widget> _screens = [
    AdminDashboardScreen(onLogout: widget.onLogout),
    const EstudiantesScreen(),
    const MateriasScreen(),
    const CarrerasScreen(),
    const CalificacionesScreen(),
    const RecomendacionesListScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(index: _idx, children: _screens),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _idx,
        onDestinationSelected: (i) => setState(() => _idx = i),
        backgroundColor: Colors.indigo.shade50,
        indicatorColor: Colors.indigo.shade100,
        destinations: const [
          NavigationDestination(
              icon: Icon(Icons.dashboard), label: 'Dashboard'),
          NavigationDestination(icon: Icon(Icons.person), label: 'Estudiantes'),
          NavigationDestination(icon: Icon(Icons.book), label: 'Materias'),
          NavigationDestination(icon: Icon(Icons.school), label: 'Carreras'),
          NavigationDestination(
              icon: Icon(Icons.grade), label: 'Calificaciones'),
          NavigationDestination(
              icon: Icon(Icons.lightbulb), label: 'Recomend.'),
        ],
      ),
    );
  }
}
