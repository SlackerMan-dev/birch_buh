#!/usr/bin/env python3
"""
Скрипт для настройки Flask приложения для внешнего доступа
Различные способы сделать ваше приложение доступным через интернет
"""

import subprocess
import sys
import os
import socket
import requests
import json
from pathlib import Path

def get_local_ip():
    """Получает локальный IP адрес"""
    try:
        # Создаем сокет для определения IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "127.0.0.1"

def get_external_ip():
    """Получает внешний IP адрес"""
    try:
        response = requests.get('https://api.ipify.org?format=json', timeout=5)
        return response.json()['ip']
    except:
        return "Не определен"

def setup_flask_for_external():
    """Настраивает Flask для внешнего доступа"""
    print("🔧 Настройка Flask для внешнего доступа...")
    
    # Проверяем наличие app.py
    if not os.path.exists('app.py'):
        print("❌ Файл app.py не найден")
        return False
    
    # Читаем содержимое app.py
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Проверяем, настроен ли уже внешний доступ
    if "host='0.0.0.0'" in content:
        print("✅ Flask уже настроен для внешнего доступа")
        return True
    
    # Создаем резервную копию
    backup_path = 'app.py.backup'
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"📁 Создана резервная копия: {backup_path}")
    
    # Заменяем настройки хоста
    if "app.run(debug=" in content:
        content = content.replace(
            "app.run(debug=debug_mode, host=host, port=port)",
            "app.run(debug=debug_mode, host='0.0.0.0', port=port)"
        )
    elif "app.run(" in content:
        content = content.replace(
            "app.run(",
            "app.run(host='0.0.0.0', "
        )
    else:
        print("❌ Не найдена строка запуска Flask")
        return False
    
    # Сохраняем изменения
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Flask настроен для внешнего доступа")
    return True

def create_env_file():
    """Создает файл с переменными окружения"""
    env_path = Path('.env')
    
    if env_path.exists():
        print("✅ Файл .env уже существует")
        return
    
    env_content = """# Переменные окружения для Flask приложения
# Настройки для внешнего доступа
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_ENV=production

# Пароли (ОБЯЗАТЕЛЬНО ИЗМЕНИТЕ!)
APP_PASSWORD=your_secure_password_here
ADMIN_PASSWORD=your_admin_password_here

# Секретный ключ (ОБЯЗАТЕЛЬНО ИЗМЕНИТЕ!)
SECRET_KEY=your_super_secret_key_here

# База данных
DATABASE_URL=sqlite:///arbitrage_reports.db
"""
    
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("✅ Создан файл .env с настройками")
    print("⚠️  ВАЖНО: Измените пароли в файле .env!")

def create_start_script():
    """Создает скрипт запуска"""
    script_content = """@echo off
echo 🚀 Запуск Flask приложения для внешнего доступа
echo ================================================

echo 📊 Проверка настроек...
if not exist app.py (
    echo ❌ Файл app.py не найден!
    pause
    exit /b 1
)

echo 🔧 Установка переменных окружения...
set FLASK_HOST=0.0.0.0
set FLASK_PORT=5000
set FLASK_ENV=production

echo 🚀 Запуск приложения...
python app.py

pause
"""
    
    with open('start_external.bat', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    # Создаем также Linux версию
    linux_script = """#!/bin/bash
echo "🚀 Запуск Flask приложения для внешнего доступа"
echo "================================================"

echo "📊 Проверка настроек..."
if [ ! -f app.py ]; then
    echo "❌ Файл app.py не найден!"
    exit 1
fi

echo "🔧 Установка переменных окружения..."
export FLASK_HOST=0.0.0.0
export FLASK_PORT=5000
export FLASK_ENV=production

echo "🚀 Запуск приложения..."
python3 app.py
"""
    
    with open('start_external.sh', 'w', encoding='utf-8') as f:
        f.write(linux_script)
    
    # Делаем скрипт исполняемым на Linux
    try:
        os.chmod('start_external.sh', 0o755)
    except:
        pass
    
    print("✅ Созданы скрипты запуска:")
    print("   - start_external.bat (Windows)")
    print("   - start_external.sh (Linux/Mac)")

def create_instructions():
    """Создает инструкции по настройке"""
    local_ip = get_local_ip()
    external_ip = get_external_ip()
    
    instructions = f"""# 🌐 Инструкции по настройке внешнего доступа

## 📊 Информация о сети

- **Локальный IP:** {local_ip}
- **Внешний IP:** {external_ip}
- **Порт приложения:** 5000

## 🚀 Способы доступа

### 1. Локальная сеть (LAN)
Приложение будет доступно всем устройствам в вашей сети:
- **URL:** http://{local_ip}:5000
- **Кому доступно:** Устройства в той же сети (Wi-Fi, Ethernet)

### 2. Интернет через роутер (Port Forwarding)
Для доступа из интернета настройте проброс портов:

#### Настройка роутера:
1. Откройте админ-панель роутера (обычно 192.168.1.1 или 192.168.0.1)
2. Найдите раздел "Port Forwarding" или "Проброс портов"
3. Добавьте правило:
   - **Внешний порт:** 5000
   - **Внутренний IP:** {local_ip}
   - **Внутренний порт:** 5000
   - **Протокол:** TCP

#### После настройки:
- **URL:** http://{external_ip}:5000
- **Кому доступно:** Всем в интернете

### 3. Туннелирование (Рекомендуется)
Используйте ngrok или Cloudflare Tunnel для безопасного доступа:

#### ngrok:
```bash
python setup_ngrok.py
```

#### Cloudflare Tunnel:
```bash
python setup_cloudflare.py
```

## 🔒 Безопасность

### ⚠️ ВАЖНО:
1. **Измените пароли** в файле .env
2. **Используйте HTTPS** для продакшена
3. **Настройте файрвол** на сервере
4. **Регулярно обновляйте** приложение

### Рекомендации:
- Для локальной сети: безопасно
- Для интернета: используйте туннели
- Для продакшена: используйте VPS/облако

## 🛠️ Устранение проблем

### Не работает в локальной сети:
1. Проверьте файрвол Windows/Linux
2. Убедитесь, что порт 5000 открыт
3. Проверьте антивирус

### Не работает из интернета:
1. Проверьте настройки роутера
2. Убедитесь, что провайдер не блокирует порт
3. Проверьте внешний IP (может быть динамическим)

### Общие проблемы:
- Перезапустите приложение
- Проверьте логи Flask
- Убедитесь, что база данных доступна

## 📞 Поддержка

При возникновении проблем:
1. Проверьте файлы логов
2. Убедитесь, что все зависимости установлены
3. Проверьте настройки сети
"""
    
    with open('EXTERNAL_ACCESS_GUIDE.md', 'w', encoding='utf-8') as f:
        f.write(instructions)
    
    print("✅ Создан файл EXTERNAL_ACCESS_GUIDE.md с инструкциями")

def main():
    print("🎯 Настройка Flask приложения для внешнего доступа")
    print("=" * 60)
    
    local_ip = get_local_ip()
    external_ip = get_external_ip()
    
    print(f"📊 Информация о сети:")
    print(f"   Локальный IP: {local_ip}")
    print(f"   Внешний IP: {external_ip}")
    
    print("\n🔧 Выберите способ настройки:")
    print("1. Локальная сеть (LAN) - доступ только в вашей сети")
    print("2. Интернет через роутер - требует настройки роутера")
    print("3. Туннелирование (ngrok) - простой способ")
    print("4. Туннелирование (Cloudflare) - бесплатный способ")
    print("5. Подготовить все варианты")
    
    choice = input("\nВведите номер (1-5): ").strip()
    
    if choice == '1':
        print("\n🏠 Настройка для локальной сети...")
        if setup_flask_for_external():
            print(f"\n✅ Готово! Приложение будет доступно по адресу:")
            print(f"🌐 http://{local_ip}:5000")
            print("\n📱 Поделитесь этой ссылкой с коллегами в вашей сети")
    
    elif choice == '2':
        print("\n🌍 Настройка для интернета...")
        if setup_flask_for_external():
            create_instructions()
            print(f"\n✅ Готово! После настройки роутера приложение будет доступно:")
            print(f"🌐 http://{external_ip}:5000")
            print("\n📋 Инструкции по настройке роутера в файле EXTERNAL_ACCESS_GUIDE.md")
    
    elif choice == '3':
        print("\n🚀 Запуск настройки ngrok...")
        os.system('python setup_ngrok.py')
        return
    
    elif choice == '4':
        print("\n☁️ Запуск настройки Cloudflare...")
        os.system('python setup_cloudflare.py')
        return
    
    elif choice == '5':
        print("\n🔧 Подготовка всех вариантов...")
        setup_flask_for_external()
        create_env_file()
        create_start_script()
        create_instructions()
        print("\n✅ Все готово!")
        print("📁 Созданы файлы:")
        print("   - .env (настройки)")
        print("   - start_external.bat/sh (скрипты запуска)")
        print("   - EXTERNAL_ACCESS_GUIDE.md (инструкции)")
    
    else:
        print("❌ Неверный выбор")
        return
    
    print("\n🎉 Настройка завершена!")
    print("💡 Для запуска используйте: python app.py")

if __name__ == "__main__":
    main() 