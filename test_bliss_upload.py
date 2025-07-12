import requests
from datetime import datetime
import pandas as pd
import os

def create_test_bliss_file():
    """Создает тестовый файл Bliss для проверки загрузки"""
    
    # Создаем тестовые данные
    test_data = [
        {
            'Internal id': '1322107',
            'Organization user': 'Morro_1',
            'Amount': '1479.75',
            'Crypto amount': '17.5',
            'Status': 'success',
            'Method': 'buy',
            'Creation date': '09.07.2025 13:06:02'
        },
        {
            'Internal id': '1322108',
            'Organization user': 'Morro_1',
            'Amount': '2500.00',
            'Crypto amount': '25.0',
            'Status': 'success',
            'Method': 'buy',
            'Creation date': '09.07.2025 07:01:05'
        },
        {
            'Internal id': '1322109',
            'Organization user': 'Morro_1',
            'Amount': '1800.50',
            'Crypto amount': '18.5',
            'Status': 'success',
            'Method': 'buy',
            'Creation date': '09.07.2025 06:57:56'
        },
        {
            'Internal id': '1322110',
            'Organization user': 'Morro_1',
            'Amount': '2100.25',
            'Crypto amount': '21.0',
            'Status': 'success',
            'Method': 'buy',
            'Creation date': '09.07.2025 06:55:50'
        },
        {
            'Internal id': '1322111',
            'Organization user': 'Morro_1',
            'Amount': '1950.75',
            'Crypto amount': '19.5',
            'Status': 'success',
            'Method': 'buy',
            'Creation date': '09.07.2025 06:37:46'
        },
        {
            'Internal id': '1322112',
            'Organization user': 'Morro_1',
            'Amount': '2250.00',
            'Crypto amount': '22.5',
            'Status': 'success',
            'Method': 'buy',
            'Creation date': '09.07.2025 06:13:14'
        }
    ]
    
    # Создаем DataFrame
    df = pd.DataFrame(test_data)
    
    # Создаем папку uploads если её нет
    os.makedirs('uploads', exist_ok=True)
    
    # Сохраняем в CSV файл
    filepath = 'test_bliss.csv'
    df.to_csv(filepath, index=False, sep=',')
    
    print(f"✅ Создан тестовый файл: {filepath}")
    print("📊 Содержимое файла:")
    print(df.to_string(index=False))
    
    return filepath

def test_upload_bliss():
    # Создаем тестовый файл
    filepath = create_test_bliss_file()
    
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
        'file': ('test_bliss.csv', open(filepath, 'rb'), 'text/csv')
    }
    
    # Отправляем запрос
    response = requests.post(url, data=data, files=files)
    
    # Выводим результат
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Удаляем тестовый файл
    try:
        os.remove(filepath)
        print(f"🗑️ Тестовый файл удален: {filepath}")
    except:
        pass

if __name__ == '__main__':
    test_upload_bliss() 