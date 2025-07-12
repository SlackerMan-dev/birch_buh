import os
import sys
import subprocess
import requests
from pathlib import Path

def download_pagekite():
    """Скачивает PageKite для Windows"""
    print("Скачивание PageKite...")
    
    # Скачиваем PageKite
    url = "https://pagekite.net/pk/pagekite-win32.zip"
    
    try:
        response = requests.get(url)
        zip_path = Path("pagekite.zip")
        zip_path.write_bytes(response.content)
        
        # Распаковываем
        import zipfile
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(".")
        
        # Удаляем zip
        zip_path.unlink()
        
        print("✅ PageKite установлен")
        return True
    except Exception as e:
        print(f"❌ Ошибка при скачивании: {e}")
        return False

def create_pagekite_config():
    """Создает конфигурацию PageKite"""
    config = """[defaults]
# Настройки по умолчанию
defaults = true
clean_shutdown = true
daemonize = false

[account]
# Настройки аккаунта (опционально)
# name = your-name
# secret = your-secret

[service]
# Настройки сервиса
service_on = http:localhost:5000:your-name.pagekite.me
"""
    
    config_path = Path("pagekite.ini")
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(config)
    
    print("✅ Конфигурация PageKite создана")

def create_bat_file():
    """Создает bat-файл для запуска"""
    bat_content = """@echo off
echo Starting PageKite tunnel...

:: Запускаем PageKite
pagekite.exe 5000 your-name.pagekite.me

pause
"""
    
    with open("start_pagekite.bat", "w", encoding='utf-8') as f:
        f.write(bat_content)
    
    print("✅ Файл start_pagekite.bat создан")

def main():
    print("🚀 Настройка PageKite туннеля")
    print("=" * 40)
    
    # Скачиваем PageKite
    if download_pagekite():
        # Создаем конфигурацию
        create_pagekite_config()
        
        # Создаем bat-файл
        create_bat_file()
        
        print("\n✅ Настройка завершена!")
        print("\n📋 Инструкция:")
        print("1. Зарегистрируйтесь на https://pagekite.net/")
        print("2. Получите бесплатный домен")
        print("3. Измените 'your-name' в start_pagekite.bat на ваш домен")
        print("4. Запустите Flask приложение: start_flask.bat")
        print("5. Запустите туннель: start_pagekite.bat")
        print("\n💡 Преимущества PageKite:")
        print("- Работает в России")
        print("- Бесплатный план")
        print("- Стабильный")
        print("- Можно выбрать свой домен")
    else:
        print("\n❌ Не удалось настроить PageKite")

if __name__ == "__main__":
    main() 