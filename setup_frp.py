import os
import sys
import subprocess
import requests
from pathlib import Path

def download_frp():
    """Скачивает frp для Windows"""
    print("Скачивание frp...")
    
    # Скачиваем frp
    url = "https://github.com/fatedier/frp/releases/download/v0.51.3/frp_0.51.3_windows_amd64.zip"
    
    try:
        response = requests.get(url)
        zip_path = Path("frp.zip")
        zip_path.write_bytes(response.content)
        
        # Распаковываем
        import zipfile
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(".")
        
        # Удаляем zip
        zip_path.unlink()
        
        print("✅ frp установлен")
        return True
    except Exception as e:
        print(f"❌ Ошибка при скачивании: {e}")
        return False

def create_frp_config():
    """Создает конфигурацию frp"""
    config = """[common]
server_addr = frp.freefrp.net
server_port = 7000
token = freefrp.net

[web]
type = http
local_port = 5000
custom_domains = your-name.freefrp.net
"""
    
    config_path = Path("frpc.ini")
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(config)
    
    print("✅ Конфигурация frp создана")

def create_bat_file():
    """Создает bat-файл для запуска"""
    bat_content = """@echo off
echo Starting frp tunnel...

:: Запускаем frp клиент
frpc.exe -c frpc.ini

pause
"""
    
    with open("start_frp.bat", "w", encoding='utf-8') as f:
        f.write(bat_content)
    
    print("✅ Файл start_frp.bat создан")

def main():
    print("🚀 Настройка frp туннеля")
    print("=" * 40)
    
    # Скачиваем frp
    if download_frp():
        # Создаем конфигурацию
        create_frp_config()
        
        # Создаем bat-файл
        create_bat_file()
        
        print("\n✅ Настройка завершена!")
        print("\n📋 Инструкция:")
        print("1. Зарегистрируйтесь на https://freefrp.net/")
        print("2. Получите бесплатный домен")
        print("3. Измените 'your-name' в frpc.ini на ваш домен")
        print("4. Запустите Flask приложение: start_flask.bat")
        print("5. Запустите туннель: start_frp.bat")
        print("\n💡 Преимущества frp:")
        print("- Работает в России")
        print("- Бесплатный")
        print("- Стабильный")
        print("- Китайская альтернатива")
    else:
        print("\n❌ Не удалось настроить frp")

if __name__ == "__main__":
    main() 