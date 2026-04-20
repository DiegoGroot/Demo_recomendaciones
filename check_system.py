#!/usr/bin/env python3
"""
Script de verificación pre-presentación para SIRA
Verifica que todos los componentes estén listos
"""

import os
import sys
import subprocess
import requests
from pathlib import Path

def print_status(message, status=True):
    """Imprime mensaje con color"""
    symbol = "✅" if status else "❌"
    print(f"{symbol} {message}")

def check_python():
    """Verificar Python"""
    try:
        version = sys.version
        print_status(f"Python {version.split()[0]} detectado")
        return True
    except:
        print_status("Python no encontrado", False)
        return False

def check_mysql():
    """Verificar MySQL"""
    try:
        result = subprocess.run(
            ["mysql", "-u", "root", "-e", "SELECT 1"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print_status("MySQL conectado")
            return True
    except:
        pass
    print_status("MySQL no disponible o no configurado", False)
    return False

def check_api():
    """Verificar API FastAPI"""
    try:
        # Iniciar servidor en background
        print("  Iniciando API...")
        process = subprocess.Popen(
            ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
            cwd="backend",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Esperar a que inicie
        import time
        time.sleep(2)
        
        # Verificar
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print_status("API FastAPI operativa (http://localhost:8000)")
            process.terminate()
            return True
    except Exception as e:
        print_status(f"API no disponible: {str(e)}", False)
    return False

def check_flutter():
    """Verificar Flutter"""
    try:
        result = subprocess.run(
            ["flutter", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            print_status(f"Flutter instalado: {version}")
            return True
    except:
        pass
    print_status("Flutter no encontrado", False)
    return False

def check_files():
    """Verificar archivos necesarios"""
    files = [
        "schema.sql",
        "backend/main.py",
        "backend/requirements.txt",
        "flutter_application/pubspec.yaml",
        "dashboard.html",
        "SIRA_API_TestCollection.postman_collection.json",
        "CASOS_DE_PRUEBA.html",
        "Dockerfile",
        "render.yaml"
    ]
    
    print("\n📂 Verificando archivos:")
    all_exist = True
    for file in files:
        exists = Path(file).exists()
        status = "✅" if exists else "❌"
        print(f"  {status} {file}")
        if not exists:
            all_exist = False
    
    return all_exist

def check_database():
    """Verificar BD SIRA"""
    try:
        result = subprocess.run(
            ["mysql", "-u", "root", "-e", "USE sira; SHOW TABLES;"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            tables = result.stdout.count("estudiante") + result.stdout.count("carrera")
            if tables > 0:
                print_status("Base de datos SIRA existe y tiene tablas")
                return True
    except:
        pass
    print_status("Base de datos SIRA no configurada", False)
    return False

def main():
    """Ejecutar todas las verificaciones"""
    print("=" * 60)
    print("🧪 VERIFICACIÓN PRE-PRESENTACIÓN SIRA")
    print("=" * 60)
    print()
    
    print("🔍 Verificando componentes:\n")
    
    checks = {
        "Python": check_python(),
        "MySQL": check_mysql(),
        "Base de Datos SIRA": check_database(),
        "Flask/FastAPI": check_api(),
        "Flutter": check_flutter(),
    }
    
    print()
    success = check_files()
    
    print()
    print("=" * 60)
    print("📊 RESUMEN")
    print("=" * 60)
    
    total = len(checks)
    passed = sum(1 for v in checks.values() if v)
    
    print(f"Componentes: {passed}/{total} ✨")
    
    if passed >= 4:
        print("\n✅ Sistema LISTO para presentación!")
        print("\n📋 Próximos pasos:")
        print("  1. Abrir dashboard.html en navegador")
        print("  2. Iniciar API: python -m uvicorn main:app --reload (en backend/)")
        print("  3. Conectar base de datos MySQL")
        print("  4. Compilar APK: flutter build apk --release")
        print("  5. ¡Presentar! 🚀")
    else:
        print("\n⚠️  Faltan algunos componentes. Revisa arriba.")
    
    print()

if __name__ == "__main__":
    main()
