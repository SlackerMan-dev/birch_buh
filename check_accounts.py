import sqlite3

def check_accounts():
    conn = sqlite3.connect('arbitrage_reports.db')
    cursor = conn.cursor()
    
    # Получаем все аккаунты
    cursor.execute('''
        SELECT a.id, a.platform, a.account_name, a.is_active, e.name as employee_name
        FROM account a
        LEFT JOIN employee e ON a.employee_id = e.id
        ORDER BY a.platform, a.account_name
    ''')
    
    accounts = cursor.fetchall()
    
    print('ID | Platform | Account Name | Active | Employee')
    print('-' * 80)
    
    for acc in accounts:
        print(f'{acc[0]} | {acc[1]} | {acc[2]} | {acc[3]} | {acc[4]}')
    
    print(f'\nВсего найдено аккаунтов: {len(accounts)}')
    
    conn.close()

if __name__ == '__main__':
    check_accounts() 