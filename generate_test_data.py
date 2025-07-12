#!/usr/bin/env python3
"""
Скрипт для генерации тестовых данных для системы отчетности арбитража (новая структура)
"""

from app import app, db, Employee, Account, ShiftReport
from datetime import datetime, timedelta
import random
import json

def generate_test_data():
    with app.app_context():
        db.session.query(ShiftReport).delete()
        db.session.query(Account).delete()
        db.session.query(Employee).delete()
        db.session.commit()
        
        # Сотрудники
        employees = [
            Employee(name="Алексей Петров", shift="morning"),
            Employee(name="Мария Сидорова", shift="morning"),
            Employee(name="Дмитрий Козлов", shift="evening"),
            Employee(name="Анна Волкова", shift="evening"),
            Employee(name="Сергей Морозов", shift="morning"),
        ]
        for emp in employees:
            db.session.add(emp)
        db.session.commit()
        
        # Аккаунты (по 2 на каждую площадку для каждого сотрудника)
        platforms = ["bybit", "htx", "bliss", "gate"]
        accounts = []
        for emp in employees:
            for platform in platforms:
                for i in range(1, 3):
                    acc = Account(employee_id=emp.id, platform=platform, account_name=f"{platform}_acc_{i}_{emp.id}")
                    db.session.add(acc)
                    accounts.append(acc)
        db.session.commit()
        
        # Генерируем отчеты за 10 дней
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=10)
        for i in range(10):
            current_date = start_date + timedelta(days=i)
            for emp in employees:
                # Выбираем случайные аккаунты для каждой площадки
                balances = {}
                for platform in platforms:
                    accs = [a for a in accounts if a.employee_id == emp.id and a.platform == platform]
                    balances[platform] = [
                        {"account_id": a.id, "account_name": a.account_name, "balance": round(random.uniform(100, 1000), 2)}
                        for a in random.sample(accs, k=random.randint(1, 2))
                    ]
                # СКАМ и ПЕРЕВОДЫ
                scam_amount = round(random.uniform(0, 200), 2) if random.random() < 0.2 else 0
                scam_comment = "Случай скам" if scam_amount else ""
                transfer_amount = round(random.uniform(0, 500), 2) if random.random() < 0.3 else 0
                transfer_comment = "Пополнение с карты" if transfer_amount else ""
                report = ShiftReport(
                    employee_id=emp.id,
                    shift_date=current_date,
                    shift_type=emp.shift,
                    total_requests=random.randint(10, 40),
                    balances_json=json.dumps(balances, ensure_ascii=False),
                    scam_amount=scam_amount,
                    scam_comment=scam_comment,
                    transfer_amount=transfer_amount,
                    transfer_comment=transfer_comment
                )
                db.session.add(report)
        db.session.commit()
        print("✅ Тестовые данные успешно сгенерированы!")
        print(f"📊 Создано:")
        print(f"   - {len(employees)} сотрудников")
        print(f"   - {len(accounts)} аккаунтов")
        print(f"   - ~{len(employees) * 10} отчетов за 10 дней")

if __name__ == "__main__":
    generate_test_data() 