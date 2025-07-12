#!/usr/bin/env python3
"""
Скрипт применения всех оптимизаций
Автоматически применяет все улучшения безопасности и производительности
"""

import os
import shutil
import sqlite3
import sys
from datetime import datetime

def backup_file(filepath):
    """Создает резервную копию файла"""
    if os.path.exists(filepath):
        backup_path = f"{filepath}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(filepath, backup_path)
        print(f"✓ Создана резервная копия: {backup_path}")
        return True
    return False

def apply_template_optimization():
    """Применяет оптимизированный шаблон"""
    print("\n🔄 Применение оптимизированного шаблона...")
    
    original_template = "templates/index.html"
    optimized_template = "templates/index_optimized.html"
    
    if not os.path.exists(optimized_template):
        print(f"❌ Оптимизированный шаблон не найден: {optimized_template}")
        return False
    
    # Создаем резервную копию
    if os.path.exists(original_template):
        backup_file(original_template)
    
    # Заменяем шаблон
    shutil.copy2(optimized_template, original_template)
    print(f"✅ Шаблон заменен на оптимизированную версию")
    return True

def apply_database_optimization():
    """Применяет оптимизацию базы данных"""
    print("\n🔄 Применение оптимизации базы данных...")
    
    db_path = 'arbitrage_reports.db'
    
    if not os.path.exists(db_path):
        print(f"⚠️  База данных не найдена: {db_path}")
        print("   Запустите приложение сначала для создания БД")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверяем существование таблиц
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        if not tables:
            print("⚠️  Таблицы не найдены в базе данных")
            conn.close()
            return False
        
        print(f"✓ Найдены таблицы: {', '.join(tables)}")
        
        # Индексы для оптимизации
        indexes = [
            ("idx_shift_reports_employee_date", "shift_reports", "employee_id, shift_date"),
            ("idx_shift_reports_date_type", "shift_reports", "shift_date, shift_type"),
            ("idx_shift_reports_date_desc", "shift_reports", "shift_date DESC"),
            ("idx_shift_reports_employee_id", "shift_reports", "employee_id"),
            ("idx_shift_reports_complex", "shift_reports", "shift_date, shift_type, employee_id"),
            ("idx_employees_name", "employees", "name"),
            ("idx_employees_telegram", "employees", "telegram"),
            ("idx_accounts_platform", "accounts", "platform"),
            ("idx_accounts_employee_id", "accounts", "employee_id"),
            ("idx_accounts_platform_employee", "accounts", "platform, employee_id"),
            ("idx_initial_balances_platform", "initial_balances", "platform"),
            ("idx_initial_balances_account_name", "initial_balances", "account_name"),
        ]
        
        created_count = 0
        
        for index_name, table_name, columns in indexes:
            if table_name in tables:
                try:
                    sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({columns})"
                    cursor.execute(sql)
                    print(f"✓ Создан индекс {index_name}")
                    created_count += 1
                except sqlite3.Error as e:
                    print(f"⚠️  Ошибка создания индекса {index_name}: {e}")
        
        # Анализируем таблицы
        for table in tables:
            try:
                cursor.execute(f"ANALYZE {table}")
                print(f"✓ Проанализирована таблица {table}")
            except sqlite3.Error as e:
                print(f"⚠️  Ошибка анализа таблицы {table}: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Создано индексов: {created_count}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при оптимизации БД: {e}")
        return False

def create_env_file():
    """Создает .env файл из примера"""
    print("\n🔄 Создание файла конфигурации...")
    
    env_example = "env.example"
    env_file = ".env"
    
    if not os.path.exists(env_example):
        print(f"❌ Файл примера не найден: {env_example}")
        return False
    
    if os.path.exists(env_file):
        print(f"⚠️  Файл .env уже существует")
        return True
    
    shutil.copy2(env_example, env_file)
    print(f"✅ Создан файл .env")
    print("⚠️  ВНИМАНИЕ: Отредактируйте .env файл и установите реальные пароли!")
    return True

def update_app_imports():
    """Обновляет импорты в app.py для использования оптимизированных утилит"""
    print("\n🔄 Обновление импортов в app.py...")
    
    app_file = "app.py"
    
    if not os.path.exists(app_file):
        print(f"❌ Файл app.py не найден")
        return False
    
    # Создаем резервную копию
    backup_file(app_file)
    
    # Читаем содержимое файла
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Заменяем импорты
    if "from utils import" in content:
        content = content.replace("from utils import", "from utils_optimized import")
        print("✓ Обновлен импорт utils на utils_optimized")
    elif "import utils" in content:
        content = content.replace("import utils", "import utils_optimized as utils")
        print("✓ Обновлен импорт utils на utils_optimized")
    else:
        print("⚠️  Импорты utils не найдены в app.py")
    
    # Записываем обновленное содержимое
    with open(app_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Файл app.py обновлен")
    return True

def main():
    """Основная функция применения оптимизаций"""
    print("🚀 Применение оптимизаций P2P арбитражной системы")
    print("=" * 60)
    
    success_count = 0
    total_steps = 4
    
    # 1. Создание .env файла
    if create_env_file():
        success_count += 1
    
    # 2. Применение оптимизированного шаблона
    if apply_template_optimization():
        success_count += 1
    
    # 3. Оптимизация базы данных
    if apply_database_optimization():
        success_count += 1
    
    # 4. Обновление импортов
    if update_app_imports():
        success_count += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Результат: {success_count}/{total_steps} шагов выполнено успешно")
    
    if success_count == total_steps:
        print("🎉 Все оптимизации применены успешно!")
        print("\n📋 Следующие шаги:")
        print("1. Отредактируйте .env файл и установите реальные пароли")
        print("2. Перезапустите приложение: python app.py")
        print("3. Проверьте работу системы")
        print("4. Ознакомьтесь с OPTIMIZATION_REPORT.md для подробностей")
    else:
        print("⚠️  Некоторые оптимизации не были применены")
        print("   Проверьте сообщения об ошибках выше")
    
    return success_count == total_steps

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 