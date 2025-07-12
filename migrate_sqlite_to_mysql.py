#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import mysql.connector
import json
from datetime import datetime
from decimal import Decimal
import os

def connect_sqlite():
    """Подключение к SQLite базе данных"""
    try:
        conn = sqlite3.connect('instance/arbitrage_reports.db')
        return conn
    except Exception as e:
        print(f"❌ Ошибка подключения к SQLite: {e}")
        return None

def connect_mysql(host, database, user, password):
    """Подключение к MySQL базе данных"""
    try:
        conn = mysql.connector.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            charset='utf8mb4'
        )
        return conn
    except Exception as e:
        print(f"❌ Ошибка подключения к MySQL: {e}")
        return None

def migrate_employees(sqlite_conn, mysql_conn):
    """Миграция сотрудников"""
    print("👥 Мигрируем сотрудников...")
    
    sqlite_cursor = sqlite_conn.cursor()
    mysql_cursor = mysql_conn.cursor()
    
    try:
        sqlite_cursor.execute("SELECT id, name, telegram, is_active, created_at, salary_percent FROM employee")
        employees = sqlite_cursor.fetchall()
        
        for employee in employees:
            mysql_cursor.execute("""
                INSERT INTO employee (id, name, telegram, is_active, created_at, salary_percent)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, employee)
        
        mysql_conn.commit()
        print(f"✅ Перенесено {len(employees)} сотрудников")
        
    except Exception as e:
        print(f"❌ Ошибка миграции сотрудников: {e}")
        mysql_conn.rollback()

def migrate_accounts(sqlite_conn, mysql_conn):
    """Миграция аккаунтов"""
    print("🏦 Мигрируем аккаунты...")
    
    sqlite_cursor = sqlite_conn.cursor()
    mysql_cursor = mysql_conn.cursor()
    
    try:
        sqlite_cursor.execute("SELECT id, employee_id, platform, account_name, is_active FROM account")
        accounts = sqlite_cursor.fetchall()
        
        for account in accounts:
            mysql_cursor.execute("""
                INSERT INTO account (id, employee_id, platform, account_name, is_active)
                VALUES (%s, %s, %s, %s, %s)
            """, account)
        
        mysql_conn.commit()
        print(f"✅ Перенесено {len(accounts)} аккаунтов")
        
    except Exception as e:
        print(f"❌ Ошибка миграции аккаунтов: {e}")
        mysql_conn.rollback()

def migrate_shift_reports(sqlite_conn, mysql_conn):
    """Миграция отчетов о сменах"""
    print("📊 Мигрируем отчеты о сменах...")
    
    sqlite_cursor = sqlite_conn.cursor()
    mysql_cursor = mysql_conn.cursor()
    
    try:
        sqlite_cursor.execute("""
            SELECT id, employee_id, shift_date, shift_type, total_requests, balances_json,
                   scam_amount, scam_comment, scam_personal, dokidka_amount, internal_transfer_amount,
                   dokidka_comment, internal_transfer_comment, bybit_file, htx_file, bliss_file,
                   start_photo, end_photo, created_at, updated_at, bybit_requests, htx_requests,
                   bliss_requests, bybit_first_trade, bybit_last_trade, htx_first_trade, htx_last_trade,
                   bliss_first_trade, bliss_last_trade, gate_first_trade, gate_last_trade,
                   appeal_amount, appeal_comment, appeal_deducted, shift_start_time, shift_end_time
            FROM shift_report
        """)
        reports = sqlite_cursor.fetchall()
        
        for report in reports:
            mysql_cursor.execute("""
                INSERT INTO shift_report (
                    id, employee_id, shift_date, shift_type, total_requests, balances_json,
                    scam_amount, scam_comment, scam_personal, dokidka_amount, internal_transfer_amount,
                    dokidka_comment, internal_transfer_comment, bybit_file, htx_file, bliss_file,
                    start_photo, end_photo, created_at, updated_at, bybit_requests, htx_requests,
                    bliss_requests, bybit_first_trade, bybit_last_trade, htx_first_trade, htx_last_trade,
                    bliss_first_trade, bliss_last_trade, gate_first_trade, gate_last_trade,
                    appeal_amount, appeal_comment, appeal_deducted, shift_start_time, shift_end_time
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, report)
        
        mysql_conn.commit()
        print(f"✅ Перенесено {len(reports)} отчетов о сменах")
        
    except Exception as e:
        print(f"❌ Ошибка миграции отчетов: {e}")
        mysql_conn.rollback()

def migrate_orders(sqlite_conn, mysql_conn):
    """Миграция ордеров"""
    print("📈 Мигрируем ордера...")
    
    sqlite_cursor = sqlite_conn.cursor()
    mysql_cursor = mysql_conn.cursor()
    
    try:
        sqlite_cursor.execute("""
            SELECT id, order_id, employee_id, platform, account_name, symbol, side,
                   quantity, price, total_usdt, fees_usdt, status, executed_at,
                   created_at, updated_at
            FROM `order`
        """)
        orders = sqlite_cursor.fetchall()
        
        for order in orders:
            mysql_cursor.execute("""
                INSERT INTO `order` (
                    id, order_id, employee_id, platform, account_name, symbol, side,
                    quantity, price, total_usdt, fees_usdt, status, executed_at,
                    created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, order)
        
        mysql_conn.commit()
        print(f"✅ Перенесено {len(orders)} ордеров")
        
    except Exception as e:
        print(f"❌ Ошибка миграции ордеров: {e}")
        mysql_conn.rollback()

def migrate_initial_balances(sqlite_conn, mysql_conn):
    """Миграция начальных балансов"""
    print("💰 Мигрируем начальные балансы...")
    
    sqlite_cursor = sqlite_conn.cursor()
    mysql_cursor = mysql_conn.cursor()
    
    try:
        sqlite_cursor.execute("SELECT id, platform, account_name, balance FROM initial_balance")
        balances = sqlite_cursor.fetchall()
        
        for balance in balances:
            mysql_cursor.execute("""
                INSERT INTO initial_balance (id, platform, account_name, balance)
                VALUES (%s, %s, %s, %s)
            """, balance)
        
        mysql_conn.commit()
        print(f"✅ Перенесено {len(balances)} начальных балансов")
        
    except Exception as e:
        print(f"❌ Ошибка миграции балансов: {e}")
        mysql_conn.rollback()

def migrate_account_balance_history(sqlite_conn, mysql_conn):
    """Миграция истории балансов аккаунтов"""
    print("📈 Мигрируем историю балансов...")
    
    sqlite_cursor = sqlite_conn.cursor()
    mysql_cursor = mysql_conn.cursor()
    
    try:
        sqlite_cursor.execute("""
            SELECT id, account_id, account_name, platform, shift_date, shift_type,
                   balance, employee_id, employee_name, balance_type
            FROM account_balance_history
        """)
        history = sqlite_cursor.fetchall()
        
        for record in history:
            mysql_cursor.execute("""
                INSERT INTO account_balance_history (
                    id, account_id, account_name, platform, shift_date, shift_type,
                    balance, employee_id, employee_name, balance_type
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, record)
        
        mysql_conn.commit()
        print(f"✅ Перенесено {len(history)} записей истории балансов")
        
    except Exception as e:
        print(f"❌ Ошибка миграции истории балансов: {e}")
        mysql_conn.rollback()

def migrate_employee_scam_history(sqlite_conn, mysql_conn):
    """Миграция истории скамов сотрудников"""
    print("⚠️ Мигрируем историю скамов...")
    
    sqlite_cursor = sqlite_conn.cursor()
    mysql_cursor = mysql_conn.cursor()
    
    try:
        sqlite_cursor.execute("""
            SELECT id, employee_id, shift_report_id, amount, comment, date, created_at
            FROM employee_scam_history
        """)
        scams = sqlite_cursor.fetchall()
        
        for scam in scams:
            mysql_cursor.execute("""
                INSERT INTO employee_scam_history (
                    id, employee_id, shift_report_id, amount, comment, date, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, scam)
        
        mysql_conn.commit()
        print(f"✅ Перенесено {len(scams)} записей истории скамов")
        
    except Exception as e:
        print(f"❌ Ошибка миграции истории скамов: {e}")
        mysql_conn.rollback()

def migrate_salary_settings(sqlite_conn, mysql_conn):
    """Миграция настроек зарплаты"""
    print("💵 Мигрируем настройки зарплаты...")
    
    sqlite_cursor = sqlite_conn.cursor()
    mysql_cursor = mysql_conn.cursor()
    
    try:
        sqlite_cursor.execute("""
            SELECT id, base_percent, min_requests_per_day, bonus_percent, 
                   bonus_requests_threshold, updated_at
            FROM salary_settings
        """)
        settings = sqlite_cursor.fetchall()
        
        for setting in settings:
            mysql_cursor.execute("""
                INSERT INTO salary_settings (
                    id, base_percent, min_requests_per_day, bonus_percent, 
                    bonus_requests_threshold, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, setting)
        
        mysql_conn.commit()
        print(f"✅ Перенесено {len(settings)} настроек зарплаты")
        
    except Exception as e:
        print(f"❌ Ошибка миграции настроек зарплаты: {e}")
        mysql_conn.rollback()

def main():
    """Основная функция миграции"""
    print("🔄 Начинаем миграцию данных из SQLite в MySQL...\n")
    
    # Подключение к SQLite
    sqlite_conn = connect_sqlite()
    if not sqlite_conn:
        return
    
    # Получение параметров MySQL
    print("Введите параметры подключения к MySQL:")
    host = input("Хост (localhost): ").strip() or "localhost"
    database = input("Имя базы данных: ").strip()
    user = input("Пользователь: ").strip()
    password = input("Пароль: ").strip()
    
    # Подключение к MySQL
    mysql_conn = connect_mysql(host, database, user, password)
    if not mysql_conn:
        sqlite_conn.close()
        return
    
    try:
        # Выполняем миграцию всех таблиц
        migrate_employees(sqlite_conn, mysql_conn)
        migrate_accounts(sqlite_conn, mysql_conn)
        migrate_shift_reports(sqlite_conn, mysql_conn)
        migrate_orders(sqlite_conn, mysql_conn)
        migrate_initial_balances(sqlite_conn, mysql_conn)
        migrate_account_balance_history(sqlite_conn, mysql_conn)
        migrate_employee_scam_history(sqlite_conn, mysql_conn)
        migrate_salary_settings(sqlite_conn, mysql_conn)
        
        print("\n✅ Миграция завершена успешно!")
        print("🌐 Теперь можете использовать MySQL базу данных на Timeweb")
        
    except Exception as e:
        print(f"\n❌ Ошибка во время миграции: {e}")
    
    finally:
        sqlite_conn.close()
        mysql_conn.close()

if __name__ == "__main__":
    main() 