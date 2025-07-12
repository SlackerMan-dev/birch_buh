#!/usr/bin/env python3
"""
Скрипт для запуска Flask приложения с ngrok туннелем
Делает ваше приложение доступным через интернет
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def download_ngrok():
    """Скачивает ngrok для Windows"""
    import requests
    
    print("Скачивание ngrok...")
    url = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip"
    
    response = requests.get(url)
    zip_path = Path("ngrok.zip")
    zip_path.write_bytes(response.content)
    
    # Распаковываем
    import zipfile
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(".")
    
    # Удаляем zip
    zip_path.unlink()
    
    print("✅ ngrok установлен")

def create_ngrok_config():
    """Создает конфигурацию ngrok"""
    config = """version: "2"
authtoken: # Добавьте ваш токен здесь
tunnels:
  flask-app:
    proto: http
    addr: 5000
    subdomain: # Опционально, для платных аккаунтов
"""
    
    config_path = Path("ngrok.yml")
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(config)
    
    print("✅ Конфигурация ngrok создана")

def create_bat_file():
    """Создает bat-файл для запуска"""
    bat_content = """@echo off
echo Starting ngrok tunnel...

:: Запускаем ngrok
ngrok.exe http 5000

pause
"""
    
    with open("start_ngrok.bat", "w", encoding='utf-8') as f:
        f.write(bat_content)
    
    print("✅ Файл start_ngrok.bat создан")

def main():
    print("🚀 Настройка ngrok туннеля")
    print("=" * 40)
    
    # Скачиваем ngrok
    download_ngrok()
    
    # Создаем конфигурацию
    create_ngrok_config()
    
    # Создаем bat-файл
    create_bat_file()
    
    print("\n✅ Настройка завершена!")
    print("\n📋 Инструкция:")
    print("1. Зарегистрируйтесь на https://ngrok.com/")
    print("2. Получите бесплатный authtoken")
    print("3. Добавьте токен в файл ngrok.yml")
    print("4. Запустите Flask приложение: start_flask.bat")
    print("5. Запустите туннель: start_ngrok.bat")
    print("\n💡 Бесплатный план ngrok:")
    print("- 1 туннель одновременно")
    print("- Случайные URL (например: https://abc123.ngrok.io)")
    print("- 40 подключений в минуту")

if __name__ == "__main__":
    main() 