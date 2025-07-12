import os
import sys
import subprocess
from pathlib import Path

def create_serveo_script():
    """Создает скрипт для Serveo"""
    script_content = """@echo off
echo Starting Serveo tunnel...

:: Используем SSH для создания туннеля
ssh -R 80:localhost:5000 serveo.net

pause
"""
    
    with open("start_serveo.bat", "w", encoding='utf-8') as f:
        f.write(script_content)
    
    print("✅ Файл start_serveo.bat создан")

def create_alternative_script():
    """Создает альтернативный скрипт с curl"""
    script_content = """@echo off
echo Starting Serveo tunnel with curl...

:: Используем curl для создания туннеля
curl -s -N -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Sec-WebSocket-Key: SGVsbG8sIHdvcmxkIQ==" -H "Sec-WebSocket-Version: 13" https://serveo.net/ssh

pause
"""
    
    with open("start_serveo_curl.bat", "w", encoding='utf-8') as f:
        f.write(script_content)
    
    print("✅ Файл start_serveo_curl.bat создан")

def main():
    print("🚀 Настройка Serveo туннеля")
    print("=" * 40)
    
    # Создаем скрипты
    create_serveo_script()
    create_alternative_script()
    
    print("\n✅ Настройка завершена!")
    print("\n📋 Инструкция:")
    print("1. Запустите Flask приложение: start_flask.bat")
    print("2. Запустите туннель: start_serveo.bat")
    print("3. Получите URL вида: https://random-name.serveo.net")
    print("\n💡 Преимущества Serveo:")
    print("- Полностью бесплатный")
    print("- Не требует регистрации")
    print("- Работает в России")
    print("- Простая настройка")
    print("- Можно задать свой поддомен")

if __name__ == "__main__":
    main() 