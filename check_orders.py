import sqlite3

def check_bliss_orders():
    conn = sqlite3.connect('arbitrage_reports.db')
    cursor = conn.cursor()
    
    # Получаем все ордера Bliss
    cursor.execute('''
        SELECT order_id, account_name, executed_at, status, total_usdt
        FROM "order"
        WHERE platform = 'bliss'
        ORDER BY executed_at
    ''')
    
    orders = cursor.fetchall()
    
    print('Order ID | Account Name | Executed At | Status | Total USDT')
    print('-' * 80)
    
    for order in orders:
        print(f'{order[0]} | {order[1]} | {order[2]} | {order[3]} | {order[4]}')
    
    print(f'\nВсего найдено ордеров: {len(orders)}')
    
    conn.close()

if __name__ == '__main__':
    check_bliss_orders() 