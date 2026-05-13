class AppConfig {
  // ─── CONFIGURACIÓN ────────────────────────────────────────────────────────

  /// Pon false para apuntar a Render; true para desarrollo local.
  static const bool useLocalhost = false;   // <── CAMBIA ESTO

  /// URL de tu backend en Render (sin barra final).
  static const String _renderUrl = 'https://demo-recomendaciones-v2.onrender.com/api';

  static const String _localUrl = 'http://10.0.2.2:8001/api';

  // ─── NO TOCAR LO DE ABAJO ─────────────────────────────────────────────────

  static String get baseUrl => useLocalhost ? _localUrl : _renderUrl;

  /// Segundos de espera antes de cancelar una petición.
  static const int timeoutSeconds = 30;
}