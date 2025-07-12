"""
Оптимизированные утилиты для расчета прибыли и балансов
с улучшенной производительностью и кэшированием
"""

import json
from decimal import Decimal
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Dict, List, Optional, Tuple
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Кэш для часто используемых данных
@lru_cache(maxsize=1000)
def find_prev_balance_cached(account_id: int, platform: str, shift_date: str, shift_type: str) -> float:
    """
    Кэшированная версия поиска предыдущего баланса
    """
    return find_prev_balance_optimized(account_id, platform, shift_date, shift_type)

def find_prev_balance_optimized(account_id: int, platform: str, shift_date: str, shift_type: str) -> float:
    """
    Оптимизированный поиск предыдущего баланса с использованием индексов
    """
    from app import db, ShiftReport, InitialBalance
    
    try:
        # Используем подзапрос для более эффективного поиска
        prev_report = db.session.query(ShiftReport).filter(
            ShiftReport.shift_date < shift_date
        ).order_by(ShiftReport.shift_date.desc(), ShiftReport.shift_type.desc()).first()
        
        if prev_report:
            try:
                balances = json.loads(prev_report.balances_json or '{}')
                platform_accounts = balances.get(platform, [])
                
                for acc in platform_accounts:
                    if acc.get('account_id') == account_id or acc.get('id') == account_id:
                        end_balance = acc.get('end_balance', 0)
                        return float(end_balance) if end_balance not in (None, '') else 0.0
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                logger.warning(f"Ошибка парсинга JSON балансов: {e}")
        
        # Если не найден предыдущий отчет, ищем в начальных балансах
        initial = db.session.query(InitialBalance).filter_by(
            platform=platform
        ).filter(
            InitialBalance.account_name.like(f'%{account_id}%')
        ).first()
        
        return float(initial.balance) if initial else 0.0
        
    except Exception as e:
        logger.error(f"Ошибка при поиске предыдущего баланса: {e}")
        return 0.0

def find_prev_balance(db_session, account_id: int, platform: str, current_report) -> float:
    """
    Совместимая функция для существующего кода
    """
    shift_date = current_report.shift_date.isoformat()
    shift_type = current_report.shift_type
    return find_prev_balance_cached(account_id, platform, shift_date, shift_type)

def calculate_report_profit_optimized(db_session, report) -> Dict[str, float]:
    """
    Оптимизированный расчет прибыли отчета с кэшированием
    """
    try:
        # Парсим балансы
        balances = json.loads(report.balances_json or '{}')
        
        total_profit = 0.0
        platform_profits = {}
        
        # Обрабатываем каждую платформу
        for platform in ['bybit', 'htx', 'bliss', 'gate']:
            platform_accounts = balances.get(platform, [])
            platform_profit = 0.0
            
            for acc in platform_accounts:
                account_id = acc.get('account_id') or acc.get('id')
                if not account_id:
                    continue
                
                # Получаем текущий и предыдущий баланс
                current_balance = float(acc.get('end_balance', 0) or 0)
                prev_balance = find_prev_balance_cached(
                    account_id, platform, 
                    report.shift_date.isoformat(), 
                    report.shift_type
                )
                
                # Рассчитываем прибыль аккаунта
                account_profit = current_balance - prev_balance
                platform_profit += account_profit
            
            platform_profits[platform] = platform_profit
            total_profit += platform_profit
        
        # Учитываем скам и переводы
        scam_amount = float(report.scam_amount or 0)
        transfer_amount = float(report.dokidka_amount or 0)
        internal_transfer = float(getattr(report, 'internal_transfer_amount', 0) or 0)
        
        # Рассчитываем итоговую прибыль
        project_profit = total_profit - scam_amount - transfer_amount
        
        # Рассчитываем зарплатную прибыль (только скам по вине сотрудника)
        personal_scam = scam_amount if getattr(report, 'scam_personal', False) else 0
        salary_profit = total_profit - personal_scam - transfer_amount
        
        return {
            'total_profit': round(total_profit, 2),
            'project_profit': round(project_profit, 2),
            'salary_profit': round(salary_profit, 2),
            'scam_amount': round(scam_amount, 2),
            'transfer_amount': round(transfer_amount, 2),
            'internal_transfer': round(internal_transfer, 2),
            'platform_profits': {k: round(v, 2) for k, v in platform_profits.items()}
        }
        
    except Exception as e:
        logger.error(f"Ошибка при расчете прибыли отчета {report.id}: {e}")
        return {
            'total_profit': 0.0,
            'project_profit': 0.0,
            'salary_profit': 0.0,
            'scam_amount': 0.0,
            'transfer_amount': 0.0,
            'internal_transfer': 0.0,
            'platform_profits': {'bybit': 0.0, 'htx': 0.0, 'bliss': 0.0, 'gate': 0.0}
        }

def calculate_report_profit(db_session, report) -> Dict[str, float]:
    """
    Совместимая функция для существующего кода
    """
    return calculate_report_profit_optimized(db_session, report)

def calculate_account_last_balance_optimized(db_session, account_id: int, platform: str, reports: List) -> float:
    """
    Оптимизированный расчет последнего баланса аккаунта
    """
    try:
        # Сортируем отчеты по дате и типу смены
        sorted_reports = sorted(reports, 
            key=lambda r: (r.shift_date, 0 if r.shift_type == 'morning' else 1), 
            reverse=True
        )
        
        # Ищем последний отчет с данным аккаунтом
        for report in sorted_reports:
            try:
                balances = json.loads(report.balances_json or '{}')
                platform_accounts = balances.get(platform, [])
                
                for acc in platform_accounts:
                    if acc.get('account_id') == account_id or acc.get('id') == account_id:
                        end_balance = acc.get('end_balance', 0)
                        return float(end_balance) if end_balance not in (None, '') else 0.0
            except (json.JSONDecodeError, ValueError, TypeError):
                continue
        
        return 0.0
        
    except Exception as e:
        logger.error(f"Ошибка при расчете последнего баланса аккаунта {account_id}: {e}")
        return 0.0

def calculate_account_last_balance(db_session, account_id: int, platform: str, reports: List) -> float:
    """
    Совместимая функция для существующего кода
    """
    return calculate_account_last_balance_optimized(db_session, account_id, platform, reports)

def group_reports_by_day_net_profit_optimized(reports: List[Dict]) -> List[Dict]:
    """
    Оптимизированная группировка отчетов по дням с расчетом прибыли
    """
    try:
        daily_profits = {}
        
        for report in reports:
            date = report.get('shift_date', '')[:10]  # Получаем только дату
            profit = report.get('net_profit', 0)
            
            if date not in daily_profits:
                daily_profits[date] = {
                    'date': date,
                    'profit': 0.0,
                    'reports_count': 0
                }
            
            daily_profits[date]['profit'] += profit
            daily_profits[date]['reports_count'] += 1
        
        # Сортируем по дате
        result = list(daily_profits.values())
        result.sort(key=lambda x: x['date'])
        
        # Округляем прибыль
        for day in result:
            day['profit'] = round(day['profit'], 2)
        
        return result
        
    except Exception as e:
        logger.error(f"Ошибка при группировке отчетов по дням: {e}")
        return []

def group_reports_by_day_net_profit(reports: List[Dict]) -> List[Dict]:
    """
    Совместимая функция для существующего кода
    """
    return group_reports_by_day_net_profit_optimized(reports)

# Дополнительные оптимизации

def bulk_calculate_profits(db_session, reports: List) -> Dict[int, Dict[str, float]]:
    """
    Массовый расчет прибыли для списка отчетов
    """
    results = {}
    
    try:
        for report in reports:
            results[report.id] = calculate_report_profit_optimized(db_session, report)
        
        return results
        
    except Exception as e:
        logger.error(f"Ошибка при массовом расчете прибыли: {e}")
        return {}

def get_employee_statistics_optimized(db_session, employee_id: int, start_date: str, end_date: str) -> Dict:
    """
    Оптимизированная статистика по сотруднику
    """
    from app import ShiftReport
    
    try:
        # Получаем отчеты одним запросом
        reports = db_session.query(ShiftReport).filter(
            ShiftReport.employee_id == employee_id,
            ShiftReport.shift_date >= start_date,
            ShiftReport.shift_date <= end_date
        ).all()
        
        if not reports:
            return {
                'total_shifts': 0,
                'total_requests': 0,
                'total_profit': 0.0,
                'avg_profit_per_shift': 0.0
            }
        
        # Рассчитываем статистику
        total_requests = sum(
            (r.bybit_requests or 0) + (r.htx_requests or 0) + (r.bliss_requests or 0) 
            for r in reports
        )
        
        # Массовый расчет прибыли
        profits = bulk_calculate_profits(db_session, reports)
        total_profit = sum(p['salary_profit'] for p in profits.values())
        
        return {
            'total_shifts': len(reports),
            'total_requests': total_requests,
            'total_profit': round(total_profit, 2),
            'avg_profit_per_shift': round(total_profit / len(reports), 2)
        }
        
    except Exception as e:
        logger.error(f"Ошибка при расчете статистики сотрудника {employee_id}: {e}")
        return {
            'total_shifts': 0,
            'total_requests': 0,
            'total_profit': 0.0,
            'avg_profit_per_shift': 0.0
        }

# Очистка кэша
def clear_cache():
    """
    Очистка кэша для обновления данных
    """
    find_prev_balance_cached.cache_clear()
    logger.info("Кэш очищен")

# Статистика кэша
def get_cache_info():
    """
    Получение информации о кэше
    """
    return {
        'find_prev_balance_cached': find_prev_balance_cached.cache_info()._asdict()
    } 