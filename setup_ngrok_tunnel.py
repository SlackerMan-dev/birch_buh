import os
import sys
import urllib.request
import zipfile
import platform

def download_ngrok():
    print("📥 Скачиваем ngrok...")
    
    # Определяем архитектуру системы
    if platform.machine().endswith('64'):
        url = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip"
    else:
        url = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-386.zip"
    
    try:
        # Скачиваем ngrok
        print("⏳ Загрузка ngrok...")
        urllib.request.urlretrieve(url, "ngrok.zip")
        
        # Распаковываем архив
        print("📦 Распаковка ngrok...")
        with zipfile.ZipFile("ngrok.zip", 'r') as zip_ref:
            zip_ref.extractall(".")
        
        # Удаляем архив
        os.remove("ngrok.zip")
        print("✅ ngrok успешно установлен")
        
        # Создаем bat-файл для запуска туннеля
        with open("start_ngrok_tunnel.bat", "w") as f:
            f.write("@echo off\n")
            f.write('echo 🚀 Запуск ngrok туннеля...\n')
            f.write('echo ❗ Для остановки туннеля закройте это окно\n')
            f.write('echo.\n')
            f.write("ngrok http 5000\n")
        
        print("\n✨ Настройка завершена!")
        print("\n📋 Инструкция по использованию:")
        print("1. Зарегистрируйтесь на ngrok.com и получите auth token")
        print("2. Выполните команду: ngrok config add-authtoken ВАШ_ТОКЕН")
        print("3. Запустите Flask-приложение (python app.py)")
        print("4. В отдельном окне запустите start_ngrok_tunnel.bat")
        print("5. Скопируйте URL из консоли (строка с https://....ngrok.io)")
        print("\n⚠️ Важно: Не закрывайте окно с туннелем, пока нужен доступ!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    download_ngrok() 