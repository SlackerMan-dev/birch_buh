#!/usr/bin/env python3
"""
Скрипт для применения миграции базы данных
Добавляет таблицу orders для хранения ордеров от расширения Bybit
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

def apply_migration():
    """Применяет миграцию для создания таблицы orders"""
    
    # Получаем URL базы данных
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///arbitrage_reports.db')
    
    try:
        # Создаем подключение к базе данных
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Проверяем, существует ли уже таблица orders
            result = conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='order'
            """))
            
            if result.fetchone():
                print("✅ Таблица 'order' уже существует")
                return
            
            # Создаем таблицу orders
            conn.execute(text("""
                CREATE TABLE "order" (
                    id INTEGER NOT NULL,
                    order_id VARCHAR(100) NOT NULL,
                    employee_id INTEGER NOT NULL,
                    platform VARCHAR(20) NOT NULL,
                    account_name VARCHAR(100) NOT NULL,
                    symbol VARCHAR(20) NOT NULL,
                    side VARCHAR(10) NOT NULL,
                    quantity NUMERIC(15, 8) NOT NULL,
                    price NUMERIC(15, 8) NOT NULL,
                    total_usdt NUMERIC(15, 2) NOT NULL,
                    fees_usdt NUMERIC(15, 2),
                    status VARCHAR(20) NOT NULL,
                    executed_at DATETIME NOT NULL,
                    created_at DATETIME,
                    updated_at DATETIME,
                    PRIMARY KEY (id),
                    FOREIGN KEY(employee_id) REFERENCES employee (id),
                    UNIQUE (order_id)
                )
            """))
            
            # Создаем индексы для оптимизации
            conn.execute(text("""
                CREATE INDEX ix_order_employee_id ON "order" (employee_id)
            """))
            
            conn.execute(text("""
                CREATE INDEX ix_order_platform ON "order" (platform)
            """))
            
            conn.execute(text("""
                CREATE INDEX ix_order_status ON "order" (status)
            """))
            
            conn.execute(text("""
                CREATE INDEX ix_order_executed_at ON "order" (executed_at)
            """))
            
            conn.commit()
            
            print("✅ Миграция успешно применена!")
            print("📊 Создана таблица 'order' с индексами")
            
    except SQLAlchemyError as e:
        print(f"❌ Ошибка при применении миграции: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("🚀 Применение миграции для таблицы orders...")
    apply_migration()
    print("✨ Готово!") 