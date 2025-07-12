#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import sqlite3
import os
import sys

def check_database():
    """Проверяет доступность базы данных"""
    try:
        db_path = "instance/arbitrage_reports.db"
        if not os.path.exists(db_path):
            print("❌ База данных не найдена")
            return False
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        conn.close()
        
        print(f"✅ База данных доступна, найдено таблиц: {len(tables)}")
        return True
    except Exception as e:
        print(f"❌ Ошибка базы данных: {e}")
        return False

def check_app_import():
    """Проверяет импорт приложения"""
    try:
        from app import app
        print("✅ Приложение импортируется успешно")
        return True
    except Exception as e:
        print(f"❌ Ошибка импорта приложения: {e}")
        return False

def check_dependencies():
    """Проверяет установленные зависимости"""
    required_packages = [
        'flask', 'flask_sqlalchemy', 'flask_cors', 
        'pandas', 'openpyxl', 'requests', 'werkzeug',
        'sqlalchemy', 'python_dateutil', 'pytz', 'alembic', 'xlrd', 'gunicorn'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Отсутствуют пакеты: {', '.join(missing_packages)}")
        return False
    else:
        print("✅ Все зависимости установлены")
        return True

def check_directories():
    """Проверяет наличие необходимых директорий"""
    required_dirs = ['uploads', 'instance', 'templates']
    missing_dirs = []
    
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            missing_dirs.append(dir_name)
    
    if missing_dirs:
        print(f"❌ Отсутствуют директории: {', '.join(missing_dirs)}")
        return False
    else:
        print("✅ Все директории на месте")
        return True

def check_config_files():
    """Проверяет наличие конфигурационных файлов"""
    required_files = ['gunicorn_config.py', 'wsgi.py', 'requirements.txt']
    missing_files = []
    
    for file_name in required_files:
        if not os.path.exists(file_name):
            missing_files.append(file_name)
    
    if missing_files:
        print(f"❌ Отсутствуют файлы: {', '.join(missing_files)}")
        return False
    else:
        print("✅ Все конфигурационные файлы на месте")
        return True

def main():
    """Основная функция проверки"""
    print("🔍 Проверяем готовность проекта к деплою...\n")
    
    checks = [
        ("База данных", check_database),
        ("Импорт приложения", check_app_import),
        ("Зависимости", check_dependencies),
        ("Директории", check_directories),
        ("Конфигурационные файлы", check_config_files)
    ]
    
    all_passed = True
    for name, check_func in checks:
        print(f"Проверяем {name}...")
        if not check_func():
            all_passed = False
        print()
    
    if all_passed:
        print("🎉 Все проверки пройдены! Проект готов к деплою.")
        print("\n📋 Следующие шаги:")
        print("1. Создайте ВМ в Yandex Cloud")
        print("2. Запустите setup_server.sh на сервере")
        print("3. Запустите deploy.sh с IP адресом сервера")
    else:
        print("❌ Некоторые проверки не пройдены. Исправьте ошибки перед деплоем.")
        sys.exit(1)

if __name__ == "__main__":
    main() 