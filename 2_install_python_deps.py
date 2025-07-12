import subprocess
import sys

def install_package(package_name, version=None):
    package = f"{package_name}=={version}" if version else package_name
    print(f"📦 Устанавливаю {package}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package_name} успешно установлен")
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка при установке {package_name}: {e}")
        return False
    return True

def main():
    print("🔧 Установка всех необходимых пакетов Python...")
    
    # Обновляем pip
    print("\n📦 Обновляем pip...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    print("✅ pip обновлен")
    
    # Список пакетов для установки
    packages = [
        ("Flask", "2.3.3"),
        ("Flask-SQLAlchemy", "3.0.5"),
        ("Flask-CORS", "4.0.0"),
        ("pandas", "2.1.1"),
        ("openpyxl", "3.1.2"),
        ("requests", "2.31.0"),
        ("Werkzeug", "2.3.7"),
        ("SQLAlchemy", "2.0.21"),
        ("python-dateutil", "2.8.2"),
        ("pytz", "2023.3.post1"),
        ("alembic", "1.12.0"),
        ("xlrd", "2.0.1")
    ]
    
    success = True
    for package, version in packages:
        if not install_package(package, version):
            success = False
    
    if success:
        print("\n🎉 Все пакеты успешно установлены!")
        print("\nТеперь можно запустить сервер командой:")
        print("python app.py")
    else:
        print("\n⚠️ Некоторые пакеты не были установлены. Проверьте ошибки выше.")

if __name__ == "__main__":
    main() 