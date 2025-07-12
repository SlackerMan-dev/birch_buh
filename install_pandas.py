import subprocess
import sys
import os

def install_pandas():
    print("🔍 Проверяем установленную версию Python...")
    python_version = sys.version.split()[0]
    print(f"✓ Используется Python {python_version}")
    
    print("\n📦 Попытка установки pandas версии 1.5.3 (стабильная версия для Windows)...")
    try:
        # Обновляем pip для избежания проблем с установкой
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        print("✓ pip обновлен до последней версии")
        
        # Устанавливаем numpy перед pandas (часто решает проблемы с установкой)
        print("\n📦 Устанавливаем numpy...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "numpy==1.23.5"])
        print("✓ numpy установлен успешно")
        
        # Устанавливаем pandas
        print("\n📦 Устанавливаем pandas...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas==1.5.3"])
        print("✓ pandas установлен успешно")
        
        # Проверяем установку
        print("\n🔍 Проверяем установку pandas...")
        import pandas as pd
        print(f"✓ pandas версии {pd.__version__} успешно установлен и готов к использованию")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Ошибка при установке: {str(e)}")
        print("\nРекомендации по устранению ошибок:")
        print("1. Убедитесь, что установлены Visual Studio Build Tools")
        print("2. Попробуйте перезапустить компьютер и запустить скрипт снова")
        print("3. Если проблема остается, попробуйте установить более раннюю версию pandas")
        
    except ImportError as e:
        print(f"\n❌ Ошибка при импорте pandas: {str(e)}")
        print("Возможно, установка прошла с ошибками")
        
    input("\nНажмите Enter для завершения...")

if __name__ == "__main__":
    install_pandas() 