class AppConfig {
  // ─── CONFIGURACIÓN ────────────────────────────────────────────────────────
  // Para desarrollo LOCAL:  useLocalhost = true
  // Para RENDER (producción): useLocalhost = false

  static const bool useLocalhost = false; // <── CAMBIA A true PARA PRUEBAS LOCALES

  // URL de tu backend en Render (sin barra final)
  static const String _renderUrl = 'https://demo-recomendaciones-v2.onrender.com/api';

  // Para Android emulator usa 10.0.2.2 (que apunta a localhost de tu PC)
  // Para dispositivo físico en la misma red, usa la IP local de tu PC, ej: 192.168.1.X
  static const String _localUrl = 'http://10.0.2.2:8001/api';

  // ─── NO TOCAR ─────────────────────────────────────────────────────────────
  static String get baseUrl => useLocalhost ? _localUrl : _renderUrl;

  /// Segundos de espera antes de cancelar una petición.
  static const int timeoutSeconds = 30;
}