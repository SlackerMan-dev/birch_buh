#!/usr/bin/env python3
"""
Простой тест Flask приложения
"""

try:
    print("🔍 Проверка Python...")
    import sys
    print(f"✅ Python версия: {sys.version}")
    
    print("\n🔍 Проверка Flask...")
    from flask import Flask
    print("✅ Flask импортирован успешно")
    
    print("\n🔍 Проверка SQLAlchemy...")
    from flask_sqlalchemy import SQLAlchemy
    print("✅ SQLAlchemy импортирован успешно")
    
    print("\n🔍 Проверка других зависимостей...")
    from datetime import datetime
    import json
    from decimal import Decimal
    import os
    print("✅ Все зависимости импортированы успешно")
    
    print("\n🚀 Создание тестового Flask приложения...")
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db = SQLAlchemy(app)
    
    @app.route('/test')
    def test():
        return "Flask работает!"
    
    print("✅ Тестовое приложение создано")
    
    print("\n🎯 Все проверки пройдены успешно!")
    print("💡 Теперь можно запускать основное приложение")
    
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("💡 Установите зависимости: pip install flask flask-sqlalchemy flask-cors")
except Exception as e:
    print(f"❌ Ошибка: {e}")
    print("💡 Проверьте настройки Python") 