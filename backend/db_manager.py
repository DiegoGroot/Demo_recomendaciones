#!/usr/bin/env python3
"""
Script para verificar y gestionar la base de datos MySQL SIRA desde terminal
"""

import mysql.connector
from mysql.connector import Error
import sys
from typing import Optional
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "sira"),
    "port": int(os.getenv("DB_PORT", 3306)),
}


def get_connection():
    """Establece conexión con MySQL"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"❌ Error de conexión: {e}")
        return None


def test_connection():
    """Verifica la conexión a la base de datos"""
    print("\n🔍 Verificando conexión a MySQL...")
    connection = get_connection()
    if connection:
        db_info = connection.get_server_info()
        print(f"✅ Conectado a MySQL Server versión {db_info}")
        connection.close()
        return True
    return False


def list_tables():
    """Lista todas las tablas de la base de datos"""
    print("\n📋 Tablas en la base de datos:")
    connection = get_connection()
    if not connection:
        return

    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = %s",
            (DB_CONFIG["database"],),
        )
        tables = cursor.fetchall()

        if tables:
            for idx, (table_name,) in enumerate(tables, 1):
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"  {idx}. {table_name} ({count} registros)")
        else:
            print("  ❌ No hay tablas")

        cursor.close()
    except Error as e:
        print(f"❌ Error: {e}")
    finally:
        connection.close()


def list_students():
    """Lista todos los estudiantes"""
    print("\n👥 Estudiantes:")
    connection = get_connection()
    if not connection:
        return

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT e.estudiante_id, e.nombre, e.correo, c.nombre as carrera, e.promedio_general
            FROM estudiante e
            LEFT JOIN carrera c ON e.carrera_id = c.carrera_id
            """
        )
        students = cursor.fetchall()

        if students:
            for student in students:
                print(
                    f"  • {student['nombre']} ({student['correo']}) - Carrera: {student['carrera']} - Promedio: {student['promedio_general']}"
                )
        else:
            print("  ❌ No hay estudiantes registrados")

        cursor.close()
    except Error as e:
        print(f"❌ Error: {e}")
    finally:
        connection.close()


def list_recommendations(student_id: Optional[int] = None):
    """Lista recomendaciones por estudiante"""
    connection = get_connection()
    if not connection:
        return

    try:
        cursor = connection.cursor(dictionary=True)

        if student_id:
            print(f"\n💡 Recomendaciones para estudiante ID {student_id}:")
            cursor.execute(
                """
                SELECT r.recomendacion_id, e.nombre, r.tipo, r.descripcion, r.prioridad, r.estado
                FROM recomendacion r
                JOIN estudiante e ON r.estudiante_id = e.estudiante_id
                WHERE r.estudiante_id = %s
                """,
                (student_id,),
            )
        else:
            print("\n💡 Todas las recomendaciones activas:")
            cursor.execute(
                """
                SELECT r.recomendacion_id, e.nombre, r.tipo, r.descripcion, r.prioridad, r.estado
                FROM recomendacion r
                JOIN estudiante e ON r.estudiante_id = e.estudiante_id
                WHERE r.estado = 'activa'
                """
            )

        recommendations = cursor.fetchall()

        if recommendations:
            for rec in recommendations:
                priority_emoji = "🔴" if rec["prioridad"] == "alta" else "🟡"
                print(
                    f"  {priority_emoji} [{rec['tipo']}] {rec['nombre']}: {rec['descripcion']}"
                )
        else:
            print("  ❌ No hay recomendaciones")

        cursor.close()
    except Error as e:
        print(f"❌ Error: {e}")
    finally:
        connection.close()


def show_statistics():
    """Muestra estadísticas generales"""
    print("\n📊 Estadísticas:")
    connection = get_connection()
    if not connection:
        return

    try:
        cursor = connection.cursor(dictionary=True)

        # Estadísticas generales
        cursor.execute("SELECT COUNT(*) as total FROM estudiante")
        total_students = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) as total FROM carrera")
        total_careers = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) as total FROM materia")
        total_subjects = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) as total FROM recomendacion WHERE estado = 'activa'")
        active_recommendations = cursor.fetchone()["total"]

        print(f"  • Total de estudiantes: {total_students}")
        print(f"  • Total de carreras: {total_careers}")
        print(f"  • Total de materias: {total_subjects}")
        print(f"  • Recomendaciones activas: {active_recommendations}")

        cursor.close()
    except Error as e:
        print(f"❌ Error: {e}")
    finally:
        connection.close()


def show_help():
    """Muestra la ayuda"""
    help_text = """
    📚 Script de Gestión de Base de Datos SIRA
    
    Uso: python db_manager.py [comando]
    
    Comandos:
      test        - Verifica la conexión a MySQL
      tables      - Lista todas las tablas
      students    - Lista todos los estudiantes
      recs        - Lista las recomendaciones activas
      recs <id>   - Lista recomendaciones de un estudiante
      stats       - Muestra estadísticas
      help        - Muestra esta ayuda
    
    Ejemplos:
      python db_manager.py test
      python db_manager.py students
      python db_manager.py recs 1
    """
    print(help_text)


def main():
    if len(sys.argv) < 2:
        show_help()
        return

    command = sys.argv[1].lower()

    if command == "test":
        test_connection()
    elif command == "tables":
        list_tables()
    elif command == "students":
        list_students()
    elif command == "recs":
        if len(sys.argv) > 2:
            try:
                student_id = int(sys.argv[2])
                list_recommendations(student_id)
            except ValueError:
                print("❌ Error: ID debe ser un número")
        else:
            list_recommendations()
    elif command == "stats":
        show_statistics()
    elif command == "help" or command == "-h" or command == "--help":
        show_help()
    else:
        print(f"❌ Comando desconocido: {command}")
        show_help()


if __name__ == "__main__":
    main()
