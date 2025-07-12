import os
import urllib.request
import subprocess
import sys

def download_and_install_vs():
    print("🔧 Установка Visual Studio Build Tools...")
    url = "https://aka.ms/vs/17/release/vs_buildtools.exe"
    installer_path = "vs_buildtools.exe"
    
    try:
        # Скачиваем установщик
        print("📥 Загружаем установщик Visual Studio Build Tools...")
        urllib.request.urlretrieve(url, installer_path)
        print("✅ Загрузка завершена!")
        
        # Запускаем установщик
        print("\n⚙️ Сейчас откроется установщик Visual Studio Build Tools")
        print("\nВАЖНО: В открывшемся окне:")
        print("1. ✔️ Выберите 'Средства сборки C++'")
        print("2. ✔️ Выберите 'Средства сборки для Windows'")
        print("3. 📥 Нажмите 'Установить' справа внизу")
        print("4. ⏳ Дождитесь завершения установки")
        print("\nПосле установки запустите скрипт: 2_install_python_deps.py")
        
        # Запускаем установщик
        os.startfile(installer_path)
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    download_and_install_vs() 