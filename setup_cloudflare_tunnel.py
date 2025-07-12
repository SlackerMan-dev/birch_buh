import os
import sys
import urllib.request
import subprocess
import platform
import zipfile
import shutil

def download_cloudflared():
    print("Скачиваем Cloudflared...")
    
    # Определяем архитектуру системы
    if platform.machine().endswith('64'):
        url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    else:
        url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-386.exe"
    
    try:
        # Скачиваем cloudflared
        print("Загрузка cloudflared...")
        urllib.request.urlretrieve(url, "cloudflared.exe")
        print("Cloudflared успешно загружен")
        
        # Создаем bat-файл для запуска туннеля
        with open("start_tunnel.bat", "w", encoding='cp866') as f:
            f.write("@echo off\n")
            f.write("echo Запуск Cloudflare туннеля...\n")
            f.write("echo Для остановки туннеля нажмите Ctrl+C\n")
            f.write("echo.\n")
            f.write("cloudflared.exe tunnel --url http://localhost:5000\n")
        
        print("\nНастройка завершена!")
        print("\nИнструкция по использованию:")
        print("1. Запустите Flask-приложение (python app.py)")
        print("2. В отдельном окне запустите start_tunnel.bat")
        print("3. Скопируйте URL из консоли и отправьте его другому человеку")
        print("\nВажно: Не закрывайте окно с туннелем, пока нужен доступ!")
        
    except Exception as e:
        print(f"Ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    download_cloudflared() 