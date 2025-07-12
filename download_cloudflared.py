#!/usr/bin/env python3
"""
Скрипт для скачивания cloudflared и настройки туннеля
"""

import urllib.request
import subprocess
import sys
import os
import time
import json
import requests

def download_cloudflared():
    """Скачивает cloudflared"""
    url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    filename = "cloudflared.exe"
    
    if os.path.exists(filename):
        print("✅ cloudflared.exe уже существует")
        return True
    
    print("📥 Скачиваю cloudflared...")
    try:
        urllib.request.urlretrieve(url, filename)
        print("✅ cloudflared скачан успешно")
        return True
    except Exception as e:
        print(f"❌ Ошибка при скачивании: {e}")
        return False

def start_flask_app():
    """Запускает Flask приложение"""
    print("🚀 Запускаю Flask приложение...")
    
    # Устанавливаем переменные окружения
    os.environ['FLASK_HOST'] = '127.0.0.1'
    os.environ['FLASK_PORT'] = '5000'
    
    # Запускаем Flask в отдельном процессе
    flask_process = subprocess.Popen([sys.executable, 'app.py'])
    
    # Ждем запуска Flask
    time.sleep(3)
    
    return flask_process

def start_cloudflare_tunnel():
    """Запускает Cloudflare туннель"""
    print("🌐 Создаю Cloudflare туннель...")
    
    # Запускаем cloudflared
    tunnel_process = subprocess.Popen(
        ['./cloudflared.exe', 'tunnel', '--url', 'http://localhost:5000'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Ждем создания туннеля
    time.sleep(5)
    
    return tunnel_process

def get_tunnel_url(process):
    """Получает URL туннеля из вывода cloudflared"""
    try:
        # Читаем вывод процесса
        output = process.stderr.read()
        if output:
            lines = output.split('\n')
            for line in lines:
                if 'https://' in line and 'trycloudflare.com' in line:
                    # Извлекаем URL
                    url = line.split('https://')[1].split()[0]
                    return f"https://{url}"
        return None
    except:
        return None

def main():
    print("🎯 Настройка доступа к Flask приложению через Cloudflare")
    print("=" * 60)
    
    # Проверяем наличие app.py
    if not os.path.exists('app.py'):
        print("❌ Файл app.py не найден в текущей папке")
        return
    
    # Скачиваем cloudflared
    if not download_cloudflared():
        return
    
    print("\n🚀 Запускаю приложение...")
    print("=" * 60)
    
    # Запускаем Flask
    flask_process = start_flask_app()
    
    # Запускаем туннель
    tunnel_process = start_cloudflare_tunnel()
    
    # Ждем и пытаемся получить URL
    time.sleep(10)
    print("\n🔍 Ищу URL туннеля...")
    print("Проверьте вывод cloudflared выше для получения URL")
    print("URL должен выглядеть как: https://random-words-1234.trycloudflare.com")
    
    print("\n📊 Локальный доступ:")
    print(f"🏠 http://localhost:5000")
    
    print("\n⚠️  Важно:")
    print("- Не закрывайте это окно")
    print("- Cloudflare Tunnel бесплатен")
    print("- URL будет временным, но работает стабильно")
    
    try:
        print("\n🛑 Нажмите Ctrl+C для остановки")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Останавливаю сервисы...")
        flask_process.terminate()
        tunnel_process.terminate()
        print("✅ Готово!")

if __name__ == "__main__":
    main() 