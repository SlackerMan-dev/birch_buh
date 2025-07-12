import sqlite3

def check_database():
    conn = sqlite3.connect('arbitrage_reports.db')
    cursor = conn.cursor()
    
    # Получаем список всех таблиц
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print('Таблицы в базе данных:')
    print('-' * 30)
    for table in tables:
        print(table[0])
        
        # Получаем структуру таблицы
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        
        print('\nКолонки:')
        for col in columns:
            print(f'  {col[1]} ({col[2]})')
        print('-' * 30)
    
    conn.close()

if __name__ == '__main__':
    check_database() 