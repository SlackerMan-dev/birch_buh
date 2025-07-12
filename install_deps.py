#!/usr/bin/env python3
"""
Скрипт для установки зависимостей для функции загрузки файлов
"""
import subprocess
import sys
import os

def install_package(package):
    """Устанавливает пакет через pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    print("🔧 Установка зависимостей для функции загрузки файлов...")
    
    packages = [
        "pandas",
        "openpyxl",
        "xlrd"
    ]
    
    success = True
    
    for package in packages:
        print(f"📦 Устанавливаю {package}...")
        if install_package(package):
            print(f"✅ {package} успешно установлен")
        else:
            print(f"❌ Ошибка установки {package}")
            success = False
    
    if success:
        print("\n🎉 Все зависимости успешно установлены!")
        print("Теперь можно запустить сервер командой: python app.py")
    else:
        print("\n❌ Некоторые зависимости не удалось установить")
        print("Попробуйте выполнить команды вручную:")
        for package in packages:
            print(f"  pip install {package}")

if __name__ == "__main__":
    main() 