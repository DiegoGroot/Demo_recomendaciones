import 'package:flutter/material.dart';
import 'screens/login_screen.dart';
import 'screens/admin_dashboard_screen.dart';
import 'screens/estudiante_home_screen.dart';
import 'screens/carreras_screen.dart';
import 'screens/estudiantes_screen.dart';
import 'screens/calificaciones_screen.dart';
import 'screens/recomendaciones_screen.dart';
import 'screens/materias_screen.dart';
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
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.indigo),
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
  UserRole? _role;

  void _onLogin(UserRole role) => setState(() => _role = role);

  void _onLogout() {
    AuthService.logout();
    setState(() => _role = null);
  }

  @override
  Widget build(BuildContext context) {
    switch (_role) {
      case UserRole.superAdmin:
        return AdminHomePage(onLogout: _onLogout);
      case UserRole.estudiante:
        return EstudianteHomeScreen(onLogout: _onLogout);
      case null:
        return LoginScreen(onLoginSuccess: _onLogin);
    }
  }
}

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
    const CarrerasScreen(),
    const MateriasScreen(),
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
          NavigationDestination(icon: Icon(Icons.dashboard), label: 'Dashboard'),
          NavigationDestination(icon: Icon(Icons.person), label: 'Estudiantes'),
          NavigationDestination(icon: Icon(Icons.school_outlined), label: 'Carreras'),
          NavigationDestination(icon: Icon(Icons.book), label: 'Materias'),
          NavigationDestination(icon: Icon(Icons.grade), label: 'Calific.'),
          NavigationDestination(icon: Icon(Icons.lightbulb), label: 'Recomend.'),
        ],
      ),
    );
  }
}