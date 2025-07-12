#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import zipfile
from datetime import datetime

def create_deployment_package():
    """Создает пакет для деплоя на Timeweb"""
    
    print("📦 Создаем пакет для деплоя на Timeweb...")
    
    # Создаем временную директорию
    temp_dir = "timeweb_deploy"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    # Файлы для копирования
    files_to_copy = [
        'app.py',
        'utils.py',
        'requirements.txt',
        'gunicorn_config.py',
        'wsgi.py',
        'check_db.py',
        'check_orders.py',
        'check_accounts.py',
        'create_test_data.py',
        'test_bliss_upload.py',
        'test_upload.py',
        'test_orders_api.py',
        'test_flask.py',
        'apply_migration.py',
        'fix_links.py',
        'download_cloudflared.py',
        'setup_external_access.py',
        'start_server.py',
        'simple_server.py',
        'config.php',
        'config.yml',
        'alembic.ini',
        'database.sql',
        'test_bliss.csv',
        'arbitrage_reports.db'
    ]
    
    # Директории для копирования
    dirs_to_copy = [
        'templates',
        'migrations',
        'bybit-extension',
        'reports-frontend',
        'src',
        'certs'
    ]
    
    # Копируем файлы
    for file in files_to_copy:
        if os.path.exists(file):
            shutil.copy2(file, temp_dir)
            print(f"✅ Скопирован файл: {file}")
        else:
            print(f"⚠️ Файл не найден: {file}")
    
    # Копируем директории
    for dir_name in dirs_to_copy:
        if os.path.exists(dir_name):
            shutil.copytree(dir_name, os.path.join(temp_dir, dir_name))
            print(f"✅ Скопирована директория: {dir_name}")
        else:
            print(f"⚠️ Директория не найдена: {dir_name}")
    
    # Создаем директории
    os.makedirs(os.path.join(temp_dir, "uploads"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "instance"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "static"), exist_ok=True)
    
    # Создаем .htaccess для Timeweb
    htaccess_content = """RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^(.*)$ wsgi.py/$1 [QSA,L]

# Настройки для Python
AddHandler wsgi-script .py
Options ExecCGI

# Максимальный размер загружаемых файлов
php_value upload_max_filesize 16M
php_value post_max_size 16M
php_value max_execution_time 300
php_value max_input_time 300
"""
    
    with open(os.path.join(temp_dir, ".htaccess"), "w", encoding="utf-8") as f:
        f.write(htaccess_content)
    
    # Создаем config_timeweb.py
    config_content = """# Конфигурация для Timeweb
import os

# Настройки базы данных Timeweb
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_NAME = os.environ.get('DB_NAME', 'your_database_name')
DB_USER = os.environ.get('DB_USER', 'your_username')
DB_PASS = os.environ.get('DB_PASS', 'your_password')

# Настройки приложения
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Blalala2')

# Пути к файлам
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
INSTANCE_PATH = os.path.join(os.path.dirname(__file__), 'instance')

# Создаем директории если не существуют
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(INSTANCE_PATH, exist_ok=True)
"""
    
    with open(os.path.join(temp_dir, "config_timeweb.py"), "w", encoding="utf-8") as f:
        f.write(config_content)
    
    # Создаем requirements_timeweb.txt (без gunicorn)
    requirements_content = """Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-CORS==4.0.0
pandas==1.5.3
openpyxl==3.1.2
requests==2.31.0
Werkzeug==2.3.7
SQLAlchemy==2.0.21
python-dateutil==2.8.2
pytz==2023.3.post1
alembic==1.12.0
xlrd==2.0.1
mysqlclient==2.1.1
"""
    
    with open(os.path.join(temp_dir, "requirements_timeweb.txt"), "w", encoding="utf-8") as f:
        f.write(requirements_content)
    
    # Создаем README для Timeweb
    readme_content = """# Деплой на Timeweb

## Инструкция по установке:

1. Загрузите все файлы в корневую директорию сайта
2. Создайте базу данных MySQL в панели Timeweb
3. Настройте переменные окружения в панели Timeweb:
   - DB_HOST
   - DB_NAME  
   - DB_USER
   - DB_PASS
   - SECRET_KEY
   - ADMIN_PASSWORD

4. Установите зависимости:
   pip install -r requirements_timeweb.txt

5. Настройте .htaccess для работы с Python

## Структура файлов:
- app.py - основное приложение
- wsgi.py - WSGI файл
- config_timeweb.py - конфигурация для Timeweb
- requirements_timeweb.txt - зависимости
- .htaccess - настройки веб-сервера

## База данных:
- Создайте MySQL базу данных в панели Timeweb
- Импортируйте структуру из database.sql
- Настройте подключение в config_timeweb.py
"""
    
    with open(os.path.join(temp_dir, "README_TIMEWEB.md"), "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    # Создаем ZIP архив
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"accounting_timeweb_{timestamp}.zip"
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, temp_dir)
                zipf.write(file_path, arcname)
    
    print(f"✅ Создан архив: {zip_filename}")
    print(f"📁 Размер архива: {os.path.getsize(zip_filename) / 1024 / 1024:.2f} МБ")
    
    # Удаляем временную директорию
    shutil.rmtree(temp_dir)
    
    return zip_filename

def create_mysql_migration():
    """Создает SQL файл для миграции с SQLite на MySQL"""
    
    print("🗄️ Создаем SQL файл для MySQL...")
    
    sql_content = """-- Миграция с SQLite на MySQL для Timeweb
-- Создание таблиц для системы бухгалтерии арбитража

-- Таблица сотрудников
CREATE TABLE employee (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    telegram VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    salary_percent FLOAT
);

-- Таблица аккаунтов
CREATE TABLE account (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT,
    platform VARCHAR(20) NOT NULL,
    account_name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (employee_id) REFERENCES employee(id)
);

-- Таблица отчетов о сменах
CREATE TABLE shift_report (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    shift_date DATE NOT NULL,
    shift_type VARCHAR(20) NOT NULL,
    total_requests INT DEFAULT 0,
    balances_json TEXT NOT NULL DEFAULT '{}',
    scam_amount DECIMAL(15,2) DEFAULT 0,
    scam_comment TEXT DEFAULT '',
    scam_personal BOOLEAN DEFAULT FALSE,
    dokidka_amount DECIMAL(15,2) DEFAULT 0,
    internal_transfer_amount DECIMAL(15,2) DEFAULT 0,
    dokidka_comment TEXT DEFAULT '',
    internal_transfer_comment TEXT DEFAULT '',
    bybit_file VARCHAR(255),
    htx_file VARCHAR(255),
    bliss_file VARCHAR(255),
    start_photo VARCHAR(255),
    end_photo VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    bybit_requests INT DEFAULT 0,
    htx_requests INT DEFAULT 0,
    bliss_requests INT DEFAULT 0,
    bybit_first_trade VARCHAR(100) DEFAULT '',
    bybit_last_trade VARCHAR(100) DEFAULT '',
    htx_first_trade VARCHAR(100) DEFAULT '',
    htx_last_trade VARCHAR(100) DEFAULT '',
    bliss_first_trade VARCHAR(100) DEFAULT '',
    bliss_last_trade VARCHAR(100) DEFAULT '',
    gate_first_trade VARCHAR(100) DEFAULT '',
    gate_last_trade VARCHAR(100) DEFAULT '',
    appeal_amount DECIMAL(15,2) DEFAULT 0,
    appeal_comment TEXT DEFAULT '',
    appeal_deducted BOOLEAN DEFAULT FALSE,
    shift_start_time DATETIME,
    shift_end_time DATETIME,
    FOREIGN KEY (employee_id) REFERENCES employee(id)
);

-- Таблица деталей ордеров
CREATE TABLE order_detail (
    id INT AUTO_INCREMENT PRIMARY KEY,
    shift_report_id INT NOT NULL,
    order_id VARCHAR(100) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    quantity DECIMAL(15,8) NOT NULL,
    price DECIMAL(15,8) NOT NULL,
    total_usdt DECIMAL(15,2) NOT NULL,
    fees_usdt DECIMAL(15,2) DEFAULT 0,
    status VARCHAR(20) NOT NULL,
    executed_at DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (shift_report_id) REFERENCES shift_report(id)
);

-- Таблица начальных балансов
CREATE TABLE initial_balance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    platform VARCHAR(20) NOT NULL,
    account_name VARCHAR(100) NOT NULL,
    balance DECIMAL(15,2) NOT NULL DEFAULT 0
);

-- Таблица истории балансов аккаунтов
CREATE TABLE account_balance_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    account_id INT,
    account_name VARCHAR(100) NOT NULL,
    platform VARCHAR(20) NOT NULL,
    shift_date DATE NOT NULL,
    shift_type VARCHAR(20) NOT NULL,
    balance DECIMAL(15,2) NOT NULL,
    employee_id INT,
    employee_name VARCHAR(100),
    balance_type VARCHAR(10) NOT NULL DEFAULT 'end',
    FOREIGN KEY (account_id) REFERENCES account(id),
    FOREIGN KEY (employee_id) REFERENCES employee(id)
);

-- Таблица ордеров
CREATE TABLE `order` (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id VARCHAR(100) NOT NULL UNIQUE,
    employee_id INT NOT NULL,
    platform VARCHAR(20) NOT NULL DEFAULT 'bybit',
    account_name VARCHAR(100) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    quantity DECIMAL(15,8) NOT NULL,
    price DECIMAL(15,8) NOT NULL,
    total_usdt DECIMAL(15,2) NOT NULL,
    fees_usdt DECIMAL(15,2) DEFAULT 0,
    status VARCHAR(20) NOT NULL,
    executed_at DATETIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employee(id)
);

-- Таблица истории скамов сотрудников
CREATE TABLE employee_scam_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    shift_report_id INT NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    comment TEXT DEFAULT '',
    date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employee(id),
    FOREIGN KEY (shift_report_id) REFERENCES shift_report(id)
);

-- Таблица настроек зарплаты
CREATE TABLE salary_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    base_percent INT NOT NULL DEFAULT 30,
    min_requests_per_day INT NOT NULL DEFAULT 50,
    bonus_percent INT NOT NULL DEFAULT 5,
    bonus_requests_threshold INT NOT NULL DEFAULT 70,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Индексы для оптимизации
CREATE INDEX idx_shift_report_employee_date ON shift_report(employee_id, shift_date);
CREATE INDEX idx_order_employee_platform ON `order`(employee_id, platform);
CREATE INDEX idx_order_executed_at ON `order`(executed_at);
CREATE INDEX idx_account_balance_history_date ON account_balance_history(shift_date);
"""
    
    with open("database_timeweb.sql", "w", encoding="utf-8") as f:
        f.write(sql_content)
    
    print("✅ Создан файл database_timeweb.sql")

def main():
    """Основная функция"""
    print("🚀 Подготовка проекта для деплоя на Timeweb...\n")
    
    # Создаем пакет для деплоя
    zip_filename = create_deployment_package()
    
    # Создаем SQL файл для MySQL
    create_mysql_migration()
    
    print("\n✅ Готово!")
    print(f"📦 Архив для загрузки: {zip_filename}")
    print("🗄️ SQL файл для базы данных: database_timeweb.sql")
    print("\n📋 Следующие шаги:")
    print("1. Зарегистрируйтесь на timeweb.ru")
    print("2. Создайте хостинг и базу данных MySQL")
    print("3. Загрузите файлы из архива на хостинг")
    print("4. Импортируйте database_timeweb.sql в MySQL")
    print("5. Настройте переменные окружения в панели Timeweb")

if __name__ == "__main__":
    main() 