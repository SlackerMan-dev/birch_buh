import os
import subprocess
import sys
import urllib.request
import tempfile

def download_vs_buildtools():
    print("Начинаем загрузку Visual Studio Build Tools...")
    url = "https://aka.ms/vs/17/release/vs_buildtools.exe"
    
    try:
        # Создаем временную директорию для загрузки
        temp_dir = tempfile.gettempdir()
        installer_path = os.path.join(temp_dir, "vs_buildtools.exe")
        
        # Загружаем установщик
        print("Загружаем установщик...")
        urllib.request.urlretrieve(url, installer_path)
        print("Загрузка завершена!")
        
        # Запускаем установку
        print("\nЗапускаем установку Visual Studio Build Tools...")
        print("ВАЖНО: После запуска установщика:")
        print("1. Выберите 'Средства сборки C++'")
        print("2. Нажмите 'Установить' справа внизу")
        print("3. Дождитесь завершения установки")
        
        # Запускаем установщик с нужными компонентами
        command = [
            installer_path,
            "--quiet",
            "--wait",
            "--add", "Microsoft.VisualStudio.Workload.VCTools",
            "--includeRecommended"
        ]
        
        subprocess.run(command, check=True)
        print("\nУстановка завершена успешно!")
        
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    download_vs_buildtools() 