import 'dart:io' show Platform;
import 'package:flutter/foundation.dart' show kIsWeb;

enum AppEnv { local, render }

class AppConfig {
 static const AppEnv _env = AppEnv.render;
  static const String _renderUrl = 'https://demo-recomendaciones-v2.onrender.com/api';

  static String get baseUrl {
    if (_env == AppEnv.render) return _renderUrl;
    
    // Puerto 8001 - Backend corriendo localmente
    if (!kIsWeb && Platform.isAndroid) return 'http://10.0.2.2:8001/api';
    return 'http://localhost:8001/api';
  }

  static const int timeoutSeconds = 15;
}
