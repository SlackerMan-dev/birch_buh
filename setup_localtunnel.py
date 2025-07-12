import os
import sys
import subprocess
from pathlib import Path

def install_localtunnel():
    """Устанавливает localtunnel через npm"""
    print("Установка localtunnel...")
    
    try:
        # Проверяем наличие Node.js
        subprocess.run(["node", "--version"], check=True, capture_output=True)
        print("✅ Node.js найден")
    except:
        print("❌ Node.js не найден")
        print("Скачайте и установите Node.js с https://nodejs.org/")
        return False
    
    try:
        # Устанавливаем localtunnel глобально
        subprocess.run(["npm", "install", "-g", "localtunnel"], check=True)
        print("✅ localtunnel установлен")
        return True
    except subprocess.CalledProcessError:
        print("❌ Ошибка при установке localtunnel")
        return False

def create_bat_file():
    """Создает bat-файл для запуска"""
    bat_content = """@echo off
echo Starting localtunnel...

:: Запускаем localtunnel
lt --port 5000

pause
"""
    
    with open("start_localtunnel.bat", "w", encoding='utf-8') as f:
        f.write(bat_content)
    
    print("✅ Файл start_localtunnel.bat создан")

def main():
    print("🚀 Настройка localtunnel")
    print("=" * 40)
    
    # Устанавливаем localtunnel
    if install_localtunnel():
        # Создаем bat-файл
        create_bat_file()
        
        print("\n✅ Настройка завершена!")
        print("\n📋 Инструкция:")
        print("1. Запустите Flask приложение: start_flask.bat")
        print("2. Запустите туннель: start_localtunnel.bat")
        print("3. Скопируйте полученный URL")
        print("\n💡 Преимущества localtunnel:")
        print("- Полностью бесплатный")
        print("- Не требует регистрации")
        print("- Работает в России")
        print("- Простая настройка")
    else:
        print("\n❌ Не удалось настроить localtunnel")

if __name__ == "__main__":
    main() 