import json
# Модели импортируйте из app.py, если они определены там
# from app import ShiftReport, InitialBalance, Account
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import date

def find_prev_balance(session: Session, account_id, platform, cur_report) -> float:
    """
    Поиск предыдущего баланса для аккаунта на платформе до cur_report.
    Сначала ищет в предыдущих отчётах, затем в InitialBalance (по id и имени).
    """
    from app import InitialBalance, Account
    prev_reports = session.query(type(cur_report)).filter(
        type(cur_report).id != cur_report.id,
        (type(cur_report).shift_date < cur_report.shift_date) |
        ((type(cur_report).shift_date == cur_report.shift_date) & (type(cur_report).shift_type == 'morning') & (cur_report.shift_type == 'evening'))
    ).order_by(type(cur_report).shift_date.desc(), type(cur_report).shift_type.desc()).all()
    for r in prev_reports:
        try:
            b = json.loads(r.balances_json or '{}')
        except:
            b = {}
        if b.get(platform):
            for a in b[platform]:
                if (a.get('account_id') or a.get('id')) == account_id:
                    return float(a.get('balance', 0))
    # Если нет предыдущего отчёта — ищем начальный баланс по id или имени
    ib = session.query(InitialBalance).filter_by(platform=platform).all()
    for bal in ib:
        if str(account_id) == str(getattr(bal, 'account_id', None)):
            return float(bal.balance)
    acc_obj = session.query(Account).filter_by(id=account_id).first()
    acc_name = acc_obj.account_name if acc_obj else None
    if acc_name:
        for bal in ib:
            if acc_name == bal.account_name:
                return float(bal.balance)
    return 0.0

def calculate_report_profit(session: Session, report) -> Dict[str, float]:
    """
    Возвращает словарь с profit (дельта), project_profit (дельта-скам-докидка-внутренний), salary_profit (дельта-докидка-внутренний-скам если scam_personal)
    Теперь дельта считается как сумма (end_balance - start_balance) по всем аккаунтам всех платформ.
    """
    try:
        balances = json.loads(report.balances_json or '{}')
    except:
        balances = {}
    
    profit = 0.0
    for platform in ['bybit','htx','bliss','gate']:
        if balances.get(platform):
            for acc in balances[platform]:
                try:
                    # Пробуем разные варианты ключей для баланса
                    start = float(acc.get('start_balance', 0) or 0)
                    end = float(acc.get('end_balance', 0) or 0)
                    
                    # Если start_balance/end_balance не найдены, пробуем найти предыдущий баланс
                    if start == 0 and end == 0:
                        # Если есть только текущий баланс, считаем разницу с предыдущим
                        current_balance = float(acc.get('balance', 0) or 0)
                        if current_balance != 0:
                            account_id = acc.get('account_id') or acc.get('id')
                            if account_id:
                                prev_balance = find_prev_balance(session, account_id, platform, report)
                                profit += current_balance - prev_balance
                                print(f"🔍 Баланс аккаунта {account_id} на {platform}: {prev_balance} -> {current_balance} (дельта: {current_balance - prev_balance})")
                        continue
                    
                    # Проверяем на аномально большие значения
                    if abs(start) > 100000:
                        print(f"⚠️  Аномально большой начальный баланс {start} в отчете {report.id}, обнуляем")
                        start = 0
                    if abs(end) > 100000:
                        print(f"⚠️  Аномально большой конечный баланс {end} в отчете {report.id}, обнуляем")
                        end = 0
                    
                    delta = end - start
                    profit += delta
                    print(f"🔍 Баланс аккаунта {acc.get('account_id', 'N/A')} на {platform}: {start} -> {end} (дельта: {delta})")
                    
                except (ValueError, TypeError) as e:
                    print(f"⚠️  Ошибка при парсинге баланса в отчете {report.id}: {e}")
                    continue
    
    try:
        dokidka = float(getattr(report, 'dokidka_amount', 0) or 0)
        internal = float(getattr(report, 'internal_transfer_amount', 0) or 0)
        scam = float(report.scam_amount or 0)
    except (ValueError, TypeError):
        dokidka = 0.0
        internal = 0.0
        scam = 0.0
    
    scam_personal = getattr(report, 'scam_personal', False)
    
    # Проверяем на аномально большие значения прибыли
    if abs(profit) > 50000:
        print(f"⚠️  Аномально большая прибыль {profit} в отчете {report.id}, обнуляем")
        profit = 0.0
    
    profit = profit - dokidka - internal
    project_profit = profit - scam
    salary_profit = profit - (scam if scam_personal else 0)
    
    return {
        'profit': round(profit, 2),
        'project_profit': round(project_profit, 2),
        'salary_profit': round(salary_profit, 2),
        'scam': round(scam, 2),
        'dokidka': round(dokidka, 2),
        'internal': round(internal, 2)
    }

def calculate_account_last_balance(session: Session, account_id: int, platform: str, reports: List) -> float:
    """
    Возвращает последний баланс аккаунта за период (или начальный баланс).
    """
    from app import InitialBalance, Account
    for r in sorted(reports, key=lambda x: (x.shift_date, 0 if x.shift_type=='morning' else 1), reverse=True):
        try:
            b = json.loads(r.balances_json or '{}')
        except:
            b = {}
        if b.get(platform):
            found = next((a for a in b[platform] if (a.get('account_id') or a.get('id')) == account_id), None)
            if found and found.get('balance') not in (None, ''):
                return float(found['balance'])
    # Если нет ни одного отчёта — берём начальный баланс
    ib = session.query(InitialBalance).filter_by(platform=platform).all()
    acc_obj = session.query(Account).filter_by(id=account_id).first()
    acc_name = acc_obj.account_name if acc_obj else None
    for bal in ib:
        if acc_name and bal.account_name == acc_name:
            return float(bal.balance)
    return 0.0

def group_reports_by_day_net_profit(reports: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Группирует отчёты по дате (YYYY-MM-DD) и суммирует net_profit за день.
    На входе — список словарей отчётов с ключом 'shift_date' и 'net_profit'.
    """
    result = {}
    for r in reports:
        d = (r['shift_date'] or '')[:10]
        result.setdefault(d, 0.0)
        result[d] += float(r.get('net_profit', 0))
    return result

def link_orders_to_employee(session: Session, shift_report) -> int:
    """Привязывает ордера к сотруднику на основе времени смены и аккаунтов"""
    from app import Account, Order  # Импортируем модели
    
    if not shift_report.shift_start_time or not shift_report.shift_end_time:
        return 0
    
    # Получаем все аккаунты сотрудника
    employee_accounts = session.query(Account).filter_by(
        employee_id=shift_report.employee_id,
        is_active=True
    ).all()
    
    account_names = [acc.account_name for acc in employee_accounts]
    
    if not account_names:
        return 0
    
    # Находим ордера в промежутке времени смены и на аккаунтах сотрудника
    orders = session.query(Order).filter(
        Order.executed_at >= shift_report.shift_start_time,
        Order.executed_at <= shift_report.shift_end_time,
        Order.account_name.in_(account_names)
    ).all()
    
    # Привязываем ордера к сотруднику
    linked_count = 0
    for order in orders:
        if order.employee_id != shift_report.employee_id:
            order.employee_id = shift_report.employee_id
            linked_count += 1
    
    session.commit()
    return linked_count

def calculate_shift_stats_from_orders(orders) -> dict:
    """Рассчитывает статистику смены на основе привязанных ордеров"""
    if not orders:
        return {
            'total_orders': 0,
            'work_hours': 0,
            'total_sales_rub': 0,
            'total_sales_usdt': 0,
            'total_purchases_rub': 0,
            'total_purchases_usdt': 0,
            'avg_sell_price': 0,
            'avg_buy_price': 0,
            'profit_usdt': 0
        }
    
    # Фильтруем только завершенные ордера
    completed_orders = [o for o in orders if o.status == 'filled']
    
    if not completed_orders:
        return {
            'total_orders': len(orders),
            'work_hours': 0,
            'total_sales_rub': 0,
            'total_sales_usdt': 0,
            'total_purchases_rub': 0,
            'total_purchases_usdt': 0,
            'avg_sell_price': 0,
            'avg_buy_price': 0,
            'profit_usdt': 0
        }
    
    # Рассчитываем время работы
    times = [o.executed_at for o in completed_orders]
    work_hours = (max(times) - min(times)).total_seconds() / 3600
    
    # Разделяем по сторонам
    sell_orders = [o for o in completed_orders if o.side == 'sell']
    buy_orders = [o for o in completed_orders if o.side == 'buy']
    
    # Продажи
    total_sales_rub = sum(float(o.total_usdt) for o in sell_orders)
    total_sales_usdt = sum(float(o.quantity) for o in sell_orders)
    
    # Покупки
    total_purchases_rub = sum(float(o.total_usdt) for o in buy_orders)
    total_purchases_usdt = sum(float(o.quantity) for o in buy_orders)
    
    # Средние цены
    avg_sell_price = total_sales_rub / total_sales_usdt if total_sales_usdt > 0 else 0
    avg_buy_price = total_purchases_rub / total_purchases_usdt if total_purchases_usdt > 0 else 0
    
    # Прибыль в USDT (покупки - продажи)
    profit_usdt = total_purchases_usdt - total_sales_usdt
    
    return {
        'total_orders': len(completed_orders),
        'work_hours': round(work_hours, 2),
        'total_sales_rub': round(total_sales_rub, 2),
        'total_sales_usdt': round(total_sales_usdt, 2),
        'total_purchases_rub': round(total_purchases_rub, 2),
        'total_purchases_usdt': round(total_purchases_usdt, 2),
        'avg_sell_price': round(avg_sell_price, 2),
        'avg_buy_price': round(avg_buy_price, 2),
        'profit_usdt': round(profit_usdt, 2)
    } 