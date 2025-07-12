#!/usr/bin/env python3
"""
Тестовый скрипт для проверки API ордеров
"""

import requests
import json
from datetime import datetime

def test_orders_api():
    """Тестирует API ордеров"""
    
    base_url = "http://localhost:5000"
    
    print("🧪 Тестирование API ордеров...")
    
    # Тест 1: Получение списка ордеров
    print("\n1. Тест получения списка ордеров:")
    try:
        response = requests.get(f"{base_url}/api/orders")
        if response.status_code == 200:
            orders = response.json()
            print(f"✅ Успешно! Найдено ордеров: {len(orders)}")
        else:
            print(f"❌ Ошибка: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка соединения: {e}")
    
    # Тест 2: Получение статистики
    print("\n2. Тест получения статистики:")
    try:
        response = requests.get(f"{base_url}/api/orders/statistics")
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Успешно! Статистика:")
            print(f"   - Всего ордеров: {stats.get('total_orders', 0)}")
            print(f"   - Общий объем: {stats.get('total_volume', 0):.2f} USDT")
            print(f"   - Комиссии: {stats.get('total_fees', 0):.2f} USDT")
        else:
            print(f"❌ Ошибка: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка соединения: {e}")
    
    # Тест 3: Получение сотрудников
    print("\n3. Тест получения сотрудников:")
    try:
        response = requests.get(f"{base_url}/api/employees")
        if response.status_code == 200:
            employees = response.json()
            print(f"✅ Успешно! Найдено сотрудников: {len(employees)}")
            if employees:
                print("   Сотрудники:")
                for emp in employees[:3]:  # Показываем первых 3
                    print(f"   - {emp.get('name', 'N/A')} (ID: {emp.get('id', 'N/A')})")
        else:
            print(f"❌ Ошибка: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка соединения: {e}")
    
    # Тест 4: Создание тестового ордера
    print("\n4. Тест создания тестового ордера:")
    try:
        # Сначала получаем сотрудника
        response = requests.get(f"{base_url}/api/employees")
        if response.status_code == 200:
            employees = response.json()
            if employees:
                employee_id = employees[0]['id']
                
                # Создаем тестовый ордер
                test_order = {
                    "order_id": f"TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "employee_id": employee_id,
                    "platform": "bybit",
                    "accountName": "Test Account",
                    "symbol": "BTC/USDT",
                    "side": "buy",
                    "quantity": 0.001,
                    "price": 50000.0,
                    "status": "filled",
                    "executed_at": datetime.now().isoformat()
                }
                
                response = requests.post(
                    f"{base_url}/api/orders",
                    headers={'Content-Type': 'application/json'},
                    json=test_order
                )
                
                if response.status_code == 201:
                    result = response.json()
                    print(f"✅ Успешно! Создан ордер ID: {result.get('id', 'N/A')}")
                else:
                    print(f"❌ Ошибка создания: HTTP {response.status_code}")
                    print(f"   Ответ: {response.text}")
            else:
                print("❌ Нет сотрудников для тестирования")
        else:
            print(f"❌ Не удалось получить сотрудников: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка создания ордера: {e}")
    
    print("\n✨ Тестирование завершено!")

if __name__ == "__main__":
    test_orders_api() 