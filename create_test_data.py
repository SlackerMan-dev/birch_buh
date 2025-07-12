import sqlite3
from datetime import datetime

def create_test_data():
    conn = sqlite3.connect('arbitrage_reports.db')
    cursor = conn.cursor()
    
    try:
        # Создаем тестового сотрудника
        cursor.execute('''
            INSERT INTO employee (name, telegram, is_active, created_at, salary_percent)
            VALUES (?, ?, ?, ?, ?)
        ''', ('Test Employee', '@test', True, datetime.now(), 10.0))
        
        employee_id = cursor.lastrowid
        print(f'Создан сотрудник с ID: {employee_id}')
        
        # Создаем тестовый аккаунт Bliss
        cursor.execute('''
            INSERT INTO account (employee_id, platform, account_name, is_active)
            VALUES (?, ?, ?, ?)
        ''', (employee_id, 'bliss', 'test_account', True))
        
        account_id = cursor.lastrowid
        print(f'Создан аккаунт с ID: {account_id}')
        
        conn.commit()
        print('✅ Тестовые данные успешно созданы')
        
    except Exception as e:
        print(f'❌ Ошибка: {str(e)}')
        conn.rollback()
    
    conn.close()

if __name__ == '__main__':
    create_test_data() 