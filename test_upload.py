#!/usr/bin/env python3
"""
Скрипт для тестирования загрузки файлов с ордерами
"""
import pandas as pd
import os
from datetime import datetime
import requests

def create_test_bybit_file():
    """Создает тестовый файл Bybit для проверки загрузки"""
    
    # Создаем тестовые данные на основе структуры из скриншота
    test_data = [
        {
            'Order No.': '191288682052605952',
            'Symbol': 'BTCUSDT', 
            'Type': 'SELL',
            'Quantity': 1479.75,
            'Price': 83.75,
            'Currency': 'RUB',
            'Time': '2025-04-17 15:12:51'
        },
        {
            'Order No.': '191288682052605953',
            'Symbol': 'ETHUSDT',
            'Type': 'BUY', 
            'Quantity': 0.5,
            'Price': 3200.00,
            'Currency': 'USDT',
            'Time': '2025-04-17 15:15:30'
        },
        {
            'Order No.': '191288682052605954',
            'Symbol': 'ADAUSDT',
            'Type': 'SELL',
            'Quantity': 1000,
            'Price': 0.45,
            'Currency': 'USDT', 
            'Time': '2025-04-17 15:20:15'
        }
    ]
    
    # Создаем DataFrame
    df = pd.DataFrame(test_data)
    
    # Сохраняем в Excel файл
    filename = f"test_bybit_orders_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = os.path.join('uploads', filename)
    
    # Создаем папку uploads если её нет
    os.makedirs('uploads', exist_ok=True)
    
    df.to_excel(filepath, index=False)
    
    print(f"✅ Создан тестовый файл: {filepath}")
    print("📊 Содержимое файла:")
    print(df.to_string(index=False))
    
    return filepath

def create_test_csv_file():
    """Создает тестовый CSV файл"""
    
    test_data = [
        {
            'Order ID': 'CSV001',
            'Symbol': 'BTCUSDT',
            'Side': 'buy',
            'Quantity': 0.001,
            'Price': 50000.00,
            'Time': '2025-01-07 12:00:00'
        },
        {
            'Order ID': 'CSV002', 
            'Symbol': 'ETHUSDT',
            'Side': 'sell',
            'Quantity': 0.1,
            'Price': 3500.00,
            'Time': '2025-01-07 12:05:00'
        }
    ]
    
    df = pd.DataFrame(test_data)
    
    filename = f"test_orders_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    filepath = os.path.join('uploads', filename)
    
    df.to_csv(filepath, index=False)
    
    print(f"✅ Создан тестовый CSV файл: {filepath}")
    print("📊 Содержимое файла:")
    print(df.to_string(index=False))
    
    return filepath

def test_parser():
    """Тестирует парсер файлов"""
    try:
        from app import parse_orders_file
        
        print("🧪 Тестируем парсер файлов...")
        
        # Создаем тестовые файлы
        excel_file = create_test_bybit_file()
        csv_file = create_test_csv_file()
        
        # Тестируем Excel файл
        print(f"\n📁 Тестируем Excel файл: {excel_file}")
        try:
            orders_excel = parse_orders_file(excel_file, 'bybit')
            print(f"✅ Найдено {len(orders_excel)} ордеров в Excel файле")
            for i, order in enumerate(orders_excel, 1):
                print(f"  {i}. {order['order_id']} - {order['symbol']} - {order['side']} - {order['quantity']} @ {order['price']}")
        except Exception as e:
            print(f"❌ Ошибка парсинга Excel: {e}")
        
        # Тестируем CSV файл
        print(f"\n📁 Тестируем CSV файл: {csv_file}")
        try:
            orders_csv = parse_orders_file(csv_file, 'bybit')
            print(f"✅ Найдено {len(orders_csv)} ордеров в CSV файле")
            for i, order in enumerate(orders_csv, 1):
                print(f"  {i}. {order['order_id']} - {order['symbol']} - {order['side']} - {order['quantity']} @ {order['price']}")
        except Exception as e:
            print(f"❌ Ошибка парсинга CSV: {e}")
        
        # Удаляем тестовые файлы
        try:
            os.remove(excel_file)
            os.remove(csv_file)
            print("\n🗑️ Тестовые файлы удалены")
        except:
            pass
            
    except ImportError:
        print("❌ Не удалось импортировать функции из app.py")
        print("   Убедитесь, что сервер запущен или добавьте app.py в PYTHONPATH")

def check_dependencies():
    """Проверяет установленные зависимости"""
    print("🔍 Проверяем зависимости...")
    
    required_packages = ['pandas', 'openpyxl', 'flask', 'flask_sqlalchemy', 'flask_cors']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - НЕ УСТАНОВЛЕН")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📦 Установите недостающие пакеты:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ Все зависимости установлены!")
    return True

def test_upload_bliss():
    url = 'http://localhost:5000/api/orders/upload'
    
    # Подготавливаем данные формы
    data = {
        'employee_id': '1',
        'platform': 'bliss',
        'account_name': 'test_account',
        'start_date': '2025-07-09T06:00',
        'end_date': '2025-07-09T15:00'
    }
    
    # Открываем файл для загрузки
    files = {
        'file': ('test_bliss.csv', open('test_bliss.csv', 'rb'), 'text/csv')
    }
    
    # Отправляем запрос
    response = requests.post(url, data=data, files=files)
    
    # Выводим результат
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")

def main():
    print("🧪 Тестирование системы загрузки ордеров")
    print("=" * 50)
    
    # Проверяем зависимости
    if not check_dependencies():
        return
    
    print()
    
    # Тестируем парсер
    test_parser()
    
    print("\n💡 Инструкции для тестирования через веб-интерфейс:")
    print("1. Запустите сервер: python app.py")
    print("2. Откройте http://localhost:5000")
    print("3. Перейдите на вкладку 'История ордеров'")
    print("4. Нажмите 'Загрузить выгрузку'")
    print("5. Выберите сотрудника, платформу и загрузите файл")
    
    print("\n📄 Создать тестовые файлы можно командой:")
    print("python test_upload.py")

if __name__ == "__main__":
    main() 