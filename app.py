from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, timedelta
import json
from decimal import Decimal
import os
from werkzeug.utils import secure_filename
from sqlalchemy import func, text
from utils import (
    find_prev_balance,
    calculate_report_profit,
    calculate_account_last_balance,
    group_reports_by_day_net_profit
)
import re

# Опциональный импорт pandas
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///arbitrage_reports.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

db = SQLAlchemy(app)
CORS(app)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'png', 'jpg', 'jpeg', 'webp', 'pdf', 'txt'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_file_size(file):
    """Дополнительная проверка размера файла"""
    if file and hasattr(file, 'content_length') and file.content_length:
        return file.content_length <= app.config['MAX_CONTENT_LENGTH']
    return True

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# --- КОНСТАНТЫ И ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
PLATFORMS = ['bybit', 'htx', 'bliss', 'gate']
ADMIN_PASSWORD = 'Blalala2'

def validate_admin_password(data):
    """Проверяет пароль администратора"""
    if not data or not data.get('password'):
        return False
    # Используем переменную окружения для пароля администратора
    admin_password = os.environ.get('ADMIN_PASSWORD', 'Blalala2')
    return data['password'] == admin_password

def convert_to_moscow_time(datetime_obj, platform):
    """
    Конвертирует время из часового пояса платформы в московское время
    
    Args:
        datetime_obj: объект datetime
        platform: название платформы ('bybit', 'htx', 'bliss')
    
    Returns:
        datetime объект в московском времени
    """
    if not datetime_obj:
        print(f"DEBUG TIMEZONE: Получен пустой datetime_obj для {platform}")
        return datetime_obj
    
    # Определяем смещение для каждой платформы относительно Москвы
    timezone_offsets = {
        'bybit': 3,   # Bybit время в UTC+0, МСК это UTC+3 → добавляем 3 часа
        'htx': -5,    # HTX время в UTC+8, МСК это UTC+3 → вычитаем 5 часов
        'bliss': 3,   # Bliss время в UTC+0, МСК это UTC+3 → добавляем 3 часа
        'gate': 0     # Gate.io: пока без смещения (можно настроить позже)
    }
    
    offset_hours = timezone_offsets.get(platform.lower(), 0)
    
    # Применяем смещение
    if offset_hours != 0:
        print(f"DEBUG TIMEZONE: Конвертируем {datetime_obj} для {platform}")
        print(f"DEBUG TIMEZONE: Смещение {offset_hours} часов")
        datetime_obj = datetime_obj + timedelta(hours=offset_hours)
        print(f"DEBUG TIMEZONE: Результат -> {datetime_obj}")
    else:
        print(f"DEBUG TIMEZONE: Нет смещения для платформы {platform}")
    
    return datetime_obj

def parse_orders_file(filepath, platform, start_date=None, end_date=None, original_filename=None):
    """Парсит файл с ордерами в зависимости от платформы"""
    try:
        # Проверяем, что файл существует
        if not os.path.exists(filepath):
            print(f"Ошибка: файл {filepath} не существует")
            return []
        
        # Определяем тип файла по расширению
        ext = os.path.splitext(filepath)[1].lower()
        
        if platform.lower() == 'bliss':
            try:
                # Пробуем разные разделители
                separators = [';', ',', '\t']
                df = None
                
                print(f"\nBLISS DEBUG: Пытаемся прочитать файл {filepath}")
                print(f"BLISS DEBUG: Размер файла: {os.path.getsize(filepath)} байт")
                
                # Читаем первые несколько строк файла для отладки
                with open(filepath, 'r', encoding='utf-8') as f:
                    print("BLISS DEBUG: Первые строки файла:")
                    for i, line in enumerate(f):
                        if i < 5:  # Показываем первые 5 строк
                            print(f"BLISS DEBUG: Строка {i+1}: {line.strip()}")
                
                for sep in separators:
                    try:
                        print(f"\nBLISS DEBUG: Пробуем разделитель '{sep}'")
                        print(f"BLISS DEBUG: Путь к файлу: {filepath}")
                        
                        # Читаем первые несколько строк для отладки
                        with open(filepath, 'r', encoding='utf-8') as f:
                            print("BLISS DEBUG: Первые 3 строки файла:")
                            for i, line in enumerate(f):
                                if i < 3:
                                    print(f"BLISS DEBUG: {line.strip()}")
                        
                        df = pd.read_csv(filepath, sep=sep, encoding='utf-8', quotechar='"', header=0)
                        print(f"BLISS DEBUG: Успешно прочитали файл")
                        print(f"BLISS DEBUG: Найдены колонки: {list(df.columns)}")
                        print(f"BLISS DEBUG: Количество строк: {len(df)}")
                        
                        # Проверяем, что нашли нужные колонки
                        required_columns = ['Creation date', 'Internal id', 'Organization user', 'Amount', 'Crypto amount', 'Status', 'Method']
                        missing_columns = [col for col in required_columns if col not in df.columns]
                        
                        if missing_columns:
                            print(f"BLISS DEBUG: Отсутствуют колонки: {missing_columns}")
                            continue
                        else:
                            print(f"BLISS DEBUG: Успешно прочитали файл с разделителем '{sep}'")
                            break
                    except Exception as e:
                        print(f"BLISS DEBUG: Не удалось прочитать файл с разделителем '{sep}': {str(e)}")
                        continue
                
                if df is None:
                    print("BLISS DEBUG: Не удалось прочитать файл ни с одним разделителем")
                    return []
                
                orders_data = []
                for _, row in df.iterrows():
                    try:
                        # Получаем необходимые поля
                        order_id = str(row['Internal id']).strip()
                        account_name = str(row['Organization user']).strip()
                        amount = str(row['Amount']).strip().replace(' ', '').replace(',', '.')
                        crypto_amount = str(row['Crypto amount']).strip().replace(' ', '').replace(',', '.')
                        status = str(row['Status']).strip()
                        method = str(row['Method']).strip()  # Добавляем поле Method
                        
                        print(f"\nBLISS DEBUG: Обрабатываем строку:")
                        print(f"BLISS DEBUG: order_id = {order_id}")
                        print(f"BLISS DEBUG: account_name = {account_name}")
                        print(f"BLISS DEBUG: amount = {amount}")
                        print(f"BLISS DEBUG: crypto_amount = {crypto_amount}")
                        print(f"BLISS DEBUG: status = {status}")
                        print(f"BLISS DEBUG: method = {method}")
                        
                        # Определяем сторону ордера на основе метода
                        if method.lower() in ['sell', 'продажа', 'продать']:
                            side = 'sell'
                        else:
                            side = 'buy'
                        
                        # Получаем время создания
                        creation_date = str(row['Creation date']).strip()
                        if creation_date:
                            try:
                                print(f"BLISS DEBUG: Исходная строка даты: '{creation_date}'")
                                executed_at = datetime.strptime(creation_date, '%d.%m.%Y %H:%M:%S')
                                print(f"BLISS DEBUG: Распарсенная дата: {executed_at}")
                                
                                # Конвертируем время в московское
                                executed_at = convert_to_moscow_time(executed_at, platform)
                                print(f"BLISS DEBUG: Дата в МСК: {executed_at}")
                                
                                # Фильтруем по времени, если указаны границы
                                if start_date and executed_at < start_date:
                                    print(f"BLISS DEBUG: Ордер {order_id} раньше начальной даты")
                                    continue
                                if end_date and executed_at > end_date:
                                    print(f"BLISS DEBUG: Ордер {order_id} позже конечной даты")
                                    continue
                                
                            except Exception as e:
                                print(f"BLISS DEBUG: Ошибка обработки даты: '{creation_date}', ошибка: {str(e)}")
                                executed_at = datetime.now()
                        else:
                            print(f"BLISS DEBUG: Пустая дата в строке")
                            executed_at = datetime.now()
                        
                        # Конвертируем числовые значения
                        try:
                            total_usdt = float(amount)
                            quantity = float(crypto_amount)
                            print(f"BLISS DEBUG: total_usdt = {total_usdt}, quantity = {quantity}")
                        except:
                            print(f"BLISS DEBUG: Ошибка конвертации чисел: amount={amount}, crypto_amount={crypto_amount}")
                            continue
                        
                        # Проверяем обязательные поля
                        if not order_id:
                            print(f"BLISS DEBUG: Пропускаем строку - не найден ID ордера")
                            continue
                        
                        if not account_name:
                            print(f"BLISS DEBUG: Пропускаем строку - не найдено имя аккаунта")
                            continue
                        
                        # Вычисляем цену
                        price = total_usdt / quantity if quantity > 0 else 0
                        print(f"BLISS DEBUG: Вычисленная цена: {price}")
                        
                        # Определяем статус
                        if status.lower() in ['success', 'completed', 'done']:
                            order_status = 'filled'
                        elif status.lower() in ['cancelled', 'canceled']:
                            order_status = 'canceled'
                        elif status.lower() in ['expired']:
                            order_status = 'expired'
                        elif status.lower() in ['failed']:
                            order_status = 'failed'
                        else:
                            order_status = 'pending'
                        
                        order_data = {
                            'order_id': order_id,
                            'symbol': 'USDT',
                            'side': side,
                            'quantity': quantity,
                            'price': price,
                            'total_usdt': total_usdt,
                            'fees_usdt': 0,
                            'status': order_status,
                            'executed_at': executed_at
                        }
                        
                        print(f"BLISS DEBUG: Создан order_data:")
                        for key, value in order_data.items():
                            print(f"BLISS DEBUG: {key} = {value}")
                        
                        orders_data.append(order_data)
                        print(f"BLISS DEBUG: Ордер {order_id} добавлен в список")
                        
                    except Exception as e:
                        print(f"BLISS DEBUG: Ошибка парсинга строки: {str(e)}")
                        continue
                
                print(f"BLISS DEBUG: Всего обработано {len(orders_data)} ордеров")
                return orders_data
                
            except Exception as e:
                print(f"BLISS: Ошибка чтения файла: {str(e)}")
                return []
                
        elif ext in ['.csv']:
            df = pd.read_csv(filepath)
        elif ext in ['.xlsx', '.xls']:
            df = pd.read_excel(filepath)
        else:
            raise Exception(f"Неподдерживаемый формат файла: {ext}")
        
        orders_data = []
        
        if platform.lower() == 'bybit':
            # Парсинг файла Bybit
            for _, row in df.iterrows():
                try:
                    # Извлекаем данные из строки
                    order_data = parse_bybit_order(row)
                    if order_data:
                        # Конвертируем время в московское
                        order_data['executed_at'] = convert_to_moscow_time(order_data['executed_at'], platform)
                        
                        # Фильтруем по времени, если указаны границы
                        if start_date or end_date:
                            order_time = order_data['executed_at']
                            
                            # Проверяем начальную дату
                            if start_date and order_time < start_date:
                                continue
                            
                            # Проверяем конечную дату
                            if end_date and order_time > end_date:
                                continue
                        
                        orders_data.append(order_data)
                except Exception as e:
                    print(f"Ошибка парсинга ордера Bybit: {str(e)}")
                    continue
                
        elif platform.lower() == 'htx':
            # Парсинг файла HTX
            for _, row in df.iterrows():
                try:
                    # Извлекаем данные из строки
                    order_data = parse_htx_order(row)
                    if order_data:
                        # Конвертируем время в московское
                        order_data['executed_at'] = convert_to_moscow_time(order_data['executed_at'], platform)
                        
                        # Фильтруем по времени, если указаны границы
                        if start_date or end_date:
                            order_time = order_data['executed_at']
                            
                            # Проверяем начальную дату
                            if start_date and order_time < start_date:
                                continue
                            
                            # Проверяем конечную дату
                            if end_date and order_time > end_date:
                                continue
                        
                        orders_data.append(order_data)
                except Exception as e:
                    print(f"Ошибка парсинга ордера HTX: {str(e)}")
                    continue
                
        elif platform.lower() == 'gate':
            # Парсинг файла Gate
            for _, row in df.iterrows():
                try:
                    # Извлекаем данные из строки
                    order_data = parse_gate_order(row)
                    if order_data:
                        # Конвертируем время в московское
                        order_data['executed_at'] = convert_to_moscow_time(order_data['executed_at'], platform)
                        
                        # Фильтруем по времени, если указаны границы
                        if start_date or end_date:
                            order_time = order_data['executed_at']
                            
                            # Проверяем начальную дату
                            if start_date and order_time < start_date:
                                continue
                            
                            # Проверяем конечную дату
                            if end_date and order_time > end_date:
                                continue
                        
                        orders_data.append(order_data)
                except Exception as e:
                    print(f"Ошибка парсинга ордера Gate: {str(e)}")
                    continue
        
        return orders_data
        
    except Exception as e:
        print(f"Ошибка парсинга файла: {str(e)}")
        return []

def parse_bybit_order(row):
    """Парсит строку ордера Bybit"""
    try:
        # Ищем нужные столбцы в строке
        order_id = None
        symbol = None
        side = None
        coin_amount = None  # Объем (USDT) - из Coin Amount
        price = None        # Цена - из Price
        fiat_amount = None  # Объем (RUB) - из Fiat Amount
        status = 'filled'   # Статус по умолчанию
        executed_at = None
        
        # Проверяем разные варианты названий столбцов
        for col in row.index:
            col_lower = str(col).lower().strip()
            col_value = str(row[col]).strip()
            
            # Order ID - различные варианты
            if any(x in col_lower for x in ['order no', 'order id', 'orderid', 'order_id', 'номер']):
                order_id = col_value
            
            # Symbol/Pair - торговая пара (из Cryptocurrency)
            elif any(x in col_lower for x in ['cryptocurrency', 'symbol', 'pair', 'пара', 'инструмент', 'currency', 'валюта']):
                if col_value and col_value.lower() not in ['nan', 'none', '']:
                    symbol = col_value.upper()  # Приводим к верхнему регистру
            
            # Side/Type - направление сделки
            elif any(x in col_lower for x in ['side', 'type', 'тип', 'направление']):
                side_value = col_value.lower()
                if any(x in side_value for x in ['buy', 'покупка', 'long']):
                    side = 'buy'
                elif any(x in side_value for x in ['sell', 'продажа', 'short']):
                    side = 'sell'
            
            # Coin Amount - количество криптовалюты (идет в колонку Объем USDT)
            elif any(x in col_lower for x in ['coin amount', 'coinamount', 'coin_amount']):
                try:
                    clean_value = re.sub(r'[^\d.,]', '', col_value)
                    if clean_value:
                        coin_amount = float(clean_value.replace(',', '.'))
                except:
                    pass
            
            # Price - цена (идет в колонку Цена)
            elif any(x in col_lower for x in ['price', 'цена', 'курс']):
                try:
                    clean_value = re.sub(r'[^\d.,]', '', col_value)
                    if clean_value:
                        price = float(clean_value.replace(',', '.'))
                except:
                    pass
            
            # Fiat Amount - сумма в фиатной валюте (идет в колонку Объем RUB)
            elif any(x in col_lower for x in ['fiat amount', 'fiatamount', 'fiat_amount']):
                try:
                    clean_value = re.sub(r'[^\d.,]', '', col_value)
                    if clean_value:
                        fiat_amount = float(clean_value.replace(',', '.'))
                except:
                    pass
            
            # Status - статус
            elif any(x in col_lower for x in ['status', 'статус']):
                if col_value and col_value.lower() not in ['nan', 'none', '']:
                    status = col_value.lower()
                    if 'completed' in status or 'завершен' in status:
                        status = 'filled'
                    elif 'canceled' in status or 'отменен' in status:
                        status = 'canceled'
                    elif 'pending' in status or 'ожидание' in status:
                        status = 'pending'
                    else:
                        status = 'filled'  # По умолчанию
            
            # Time - время
            elif any(x in col_lower for x in ['time', 'date', 'время', 'дата', 'created']):
                try:
                    if col_value and col_value != 'nan':
                        if PANDAS_AVAILABLE:
                            executed_at = pd.to_datetime(col_value)
                        else:
                            # Простой парсинг даты без pandas
                            executed_at = datetime.strptime(col_value, '%Y-%m-%d %H:%M:%S')
                except:
                    pass
        
        # Попытка автоматически вычислить недостающие значения
        # Вычисляем price, если есть coin_amount и fiat_amount
        if price is None and coin_amount not in [None, 0] and fiat_amount not in [None, 0]:
            try:
                price = fiat_amount / coin_amount if coin_amount else None
            except Exception as _:
                pass
        # Вычисляем fiat_amount, если есть price и coin_amount
        if fiat_amount is None and price not in [None, 0] and coin_amount not in [None, 0]:
            try:
                fiat_amount = price * coin_amount
            except Exception as _:
                pass

        # Установка значения по умолчанию для symbol
        if not symbol or str(symbol).lower() in ['nan', 'none', '']:
            symbol = 'USDT'

        # Проверяем, что все необходимые данные есть после попыток вычисления
        if not order_id or coin_amount is None or (price is None and fiat_amount is None):
            print(f"Пропускаем строку - недостаточно данных: order_id={order_id}, coin_amount={coin_amount}, price={price}, fiat_amount={fiat_amount}")
            return None
        
        # Дополнительная проверка на корректность symbol
        if symbol.lower() in ['nan', 'none', '']:
            print(f"Пропускаем строку - некорректный символ: {symbol}")
            return None
        
        # Если нет времени, используем текущее
        if not executed_at:
            executed_at = datetime.now()
        
        return {
            'order_id': order_id,
            'symbol': symbol,
            'side': side,
            'quantity': coin_amount,    # Объем (USDT) - из Coin Amount
            'price': price,            # Цена - из Price
            'total_usdt': fiat_amount, # Объем (RUB) - из Fiat Amount
            'fees_usdt': 0,
            'status': status,          # Статус - из Status
            'executed_at': executed_at
        }
        
    except Exception as e:
        print(f"Ошибка парсинга ордера Bybit: {e}")
        return None

def parse_htx_order(row):
    """Парсит строку ордера HTX с учетом специфики формата HTX"""
    try:
        # Инициализируем переменные
        order_id = None
        symbol = None
        side = None
        quantity = None     # Объем (USDT) - из Количество
        price = None        # Цена - из Цена за ед.
        total_usdt = None   # Объем (RUB) - из Общая цена
        status = 'filled'   # Статус по умолчанию
        executed_at = None
        
        # Прямой маппинг колонок HTX
        for col in row.index:
            col_str = str(col).strip()
            col_value = str(row[col]).strip()
            
            # Order ID - Номер:
            if col_str == 'Номер:':
                order_id = col_value
            
            # Symbol/Pair - Монета (USDT + RUB = USDT)
            elif col_str == 'Монета':
                if col_value and col_value.lower() not in ['nan', 'none', '']:
                    symbol = col_value.upper()  # USDT
            
            # Side/Type - Тип (Продать/Купить)
            elif col_str == 'Тип':
                if 'Продать' in col_value or 'продать' in col_value:
                    side = 'sell'
                elif 'Купить' in col_value or 'купить' in col_value:
                    side = 'buy'
            
            # Quantity - Количество
            elif col_str == 'Количество':
                try:
                    if col_value and col_value != 'nan':
                        quantity = float(col_value.replace(',', '.'))
                except:
                    pass
            
            # Price - Цена за ед.
            elif col_str == 'Цена за ед.':
                try:
                    if col_value and col_value != 'nan':
                        price = float(col_value.replace(',', '.'))
                except:
                    pass
            
            # Total - Общая цена
            elif col_str == 'Общая цена':
                try:
                    if col_value and col_value != 'nan':
                        total_usdt = float(col_value.replace(',', '.'))
                except:
                    pass
            
            # Status - Статус
            elif col_str == 'Статус':
                if col_value and col_value.lower() not in ['nan', 'none', '']:
                    if 'Завершено' in col_value or 'завершено' in col_value:
                        status = 'filled'
                    elif 'Отменено' in col_value or 'отменено' in col_value:
                        status = 'canceled'
                    elif 'Ожидание' in col_value or 'ожидание' in col_value:
                        status = 'pending'
                    else:
                        status = 'filled'  # По умолчанию
            
            # Time - Время
            elif col_str == 'Время':
                try:
                    if col_value and col_value != 'nan':
                        if PANDAS_AVAILABLE:
                            executed_at = pd.to_datetime(col_value)
                        else:
                            # Простой парсинг даты без pandas
                            executed_at = datetime.strptime(col_value, '%Y-%m-%d %H:%M:%S')
                except:
                    pass
        
        # Попытка автоматически вычислить недостающие значения
        if price is None and quantity not in [None, 0] and total_usdt not in [None, 0]:
            try:
                price = total_usdt / quantity if quantity else None
            except Exception:
                pass
        if total_usdt is None and price not in [None, 0] and quantity not in [None, 0]:
            try:
                total_usdt = price * quantity
            except Exception:
                pass

        # Устанавливаем значение символа по умолчанию, если не удалось прочитать
        if not symbol or str(symbol).lower() in ['nan', 'none', '']:
            symbol = 'USDT'

        # Проверяем, что все необходимые данные есть после вычислений
        if not order_id or quantity is None or (price is None and total_usdt is None):
            print(f"HTX: Пропускаем строку - недостаточно данных: order_id={order_id}, quantity={quantity}, price={price}, total_usdt={total_usdt}")
            return None
        
        # Дополнительная проверка на корректность symbol
        if symbol.lower() in ['nan', 'none', '']:
            print(f"HTX: Пропускаем строку - некорректный символ: {symbol}")
            return None
        
        # Если нет времени, используем текущее
        if not executed_at:
            executed_at = datetime.now()
        
        return {
            'order_id': order_id,
            'symbol': symbol,
            'side': side,
            'quantity': quantity,      # Объем (USDT) - из Количество
            'price': price,           # Цена - из Цена за ед.
            'total_usdt': total_usdt, # Объем (RUB) - из Общая цена
            'fees_usdt': 0,
            'status': status,         # Статус - из Статус
            'executed_at': executed_at
        }
        
    except Exception as e:
        print(f"Ошибка парсинга ордера HTX: {e}")
        return None

def parse_gate_order(row):
    """Парсит строку ордера Gate.io"""
    # Аналогично Bybit, но с учетом специфики Gate
    return parse_bybit_order(row)  # Пока используем тот же парсер

def parse_bliss_order(row):
    """Парсит строку ордера Bliss с учетом специфики формата Bliss"""
    try:
        # Инициализируем переменные
        order_id = None
        symbol = 'USDT'  # Всегда USDT для Bliss
        side = 'buy'     # Всегда покупка согласно описанию
        quantity = None  # Объем (USDT) - из Crypto amount
        price = None     # Цена - пропускается поле
        total_usdt = None  # Объем (RUB) - из Amount
        status = 'filled'  # Статус по умолчанию
        executed_at = None
        
        # Отладка: выводим все колонки
        print(f"BLISS DEBUG: Все колонки в строке: {list(row.index)}")
        
        for col in row.index:
            col_str = str(col).strip()
            col_value = str(row[col]).strip()
            
            print(f"BLISS DEBUG: Обрабатываем колонку '{col_str}' со значением '{col_value}'")
            
            # Order ID - Internal id
            if col_str == 'Internal id':
                order_id = col_value
                print(f"BLISS DEBUG: Найден order_id: {order_id}")
            
            # Quantity - Crypto amount
            elif col_str == 'Crypto amount':
                try:
                    if col_value and col_value != 'nan':
                        # Убираем запятые и конвертируем в float
                        quantity = float(col_value.replace(',', '.'))
                        print(f"BLISS DEBUG: Найден quantity: {quantity}")
                except:
                    pass
            
            # Total USDT - Amount
            elif col_str == 'Amount':
                try:
                    if col_value and col_value != 'nan':
                        # Убираем запятые и конвертируем в float
                        total_usdt = float(col_value.replace(',', '.'))
                        print(f"BLISS DEBUG: Найден total_usdt: {total_usdt}")
                except:
                    pass
            
            # Status - Status
            elif col_str == 'Status':
                if col_value and col_value != 'nan':
                    status_value = col_value.lower()
                    if status_value in ['success', 'completed', 'done']:
                        status = 'filled'
                    elif status_value in ['cancelled', 'canceled']:
                        status = 'canceled'
                    elif status_value in ['expired']:
                        status = 'expired'
                    elif status_value in ['failed']:
                        status = 'failed'
                    else:
                        status = 'pending'
                    print(f"BLISS DEBUG: Найден status: {status}")
            
            # Time - пробуем разные варианты названий колонок с датой
            elif col_str in ['Finish date', 'Creation date', 'Date', 'Time', 'Timestamp', 'Дата завершения', 'Время']:
                print(f"BLISS DEBUG: Найдена колонка с датой '{col_str}' со значением '{col_value}'")
                try:
                    if col_value and col_value != 'nan':
                        # Пробуем разные форматы даты
                        date_formats = [
                            '%d.%m.%Y %H:%M',
                            '%d.%m.%Y %H:%M:%S',
                            '%Y-%m-%d %H:%M:%S',
                            '%Y-%m-%d %H:%M',
                            '%d/%m/%Y %H:%M',
                            '%d-%m-%Y %H:%M'
                        ]
                        
                        for date_format in date_formats:
                            try:
                                if PANDAS_AVAILABLE:
                                    executed_at = pd.to_datetime(col_value, format=date_format)
                                else:
                                    executed_at = datetime.strptime(col_value, date_format)
                                print(f"BLISS DEBUG: Успешно распарсили дату '{col_value}' в формате '{date_format}' -> {executed_at}")
                                break
                            except:
                                continue
                        else:
                            print(f"BLISS DEBUG: Не удалось распарсить дату '{col_value}' ни в одном формате")
                except Exception as e:
                    print(f"BLISS DEBUG: Ошибка парсинга даты '{col_value}': {e}")
        
        # Вычисляем цену на основе имеющихся данных
        price = None
        if quantity is not None and total_usdt is not None and quantity > 0:
            price = total_usdt / quantity
        
        # Проверяем, что все необходимые данные есть
        if not order_id or quantity is None or total_usdt is None or price is None:
            print(f"BLISS: Пропускаем строку - недостаточно данных: order_id={order_id}, symbol={symbol}, side={side}, quantity={quantity}, price={price}, total_usdt={total_usdt}")
            return None
        
        # Если нет времени, используем текущее
        if not executed_at:
            executed_at = datetime.now()
        
        # Время будет конвертировано позже в process_platform_file
        # executed_at остаётся в исходном часовом поясе
        
        return {
            'order_id': order_id,
            'account_name': None,  # Не используем имя аккаунта из файла
            'symbol': symbol,
            'side': side,              # Всегда 'buy'
            'quantity': quantity,      # Объем (USDT) - из Crypto amount
            'price': price,            # Цена - вычисляется
            'total_usdt': total_usdt,  # Объем (RUB) - из Amount
            'fees_usdt': 0,
            'status': status,          # Статус - из Status
            'executed_at': executed_at
        }
        
    except Exception as e:
        print(f"BLISS: Ошибка парсинга строки: {str(e)}")
        return None

# Модели данных
class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    telegram = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    salary_percent = db.Column(db.Float, nullable=True)  # Новый процент для расчёта зарплаты

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True)
    platform = db.Column(db.String(20), nullable=False)  # bybit, htx, bliss, gate
    account_name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

class ShiftReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    shift_date = db.Column(db.Date, nullable=False)
    shift_type = db.Column(db.String(20), nullable=False)  # 'morning' или 'evening'
    total_requests = db.Column(db.Integer, default=0)  # всего заявок обработано
    # Балансы по аккаунтам (json: {"bybit": [{"account_id": 1, "balance": 123.45}, ...], ...})
    balances_json = db.Column(db.Text, nullable=False, default='{}')
    # СКАМ
    scam_amount = db.Column(db.Numeric(15, 2), default=0)
    scam_comment = db.Column(db.Text, default='')
    scam_personal = db.Column(db.Boolean, default=False)  # Новое поле: скам по вине сотрудника
    # ПЕРЕВОДЫ
    dokidka_amount = db.Column(db.Numeric(15, 2), default=0)  # Новое поле: докидка (внешний перевод)
    internal_transfer_amount = db.Column(db.Numeric(15, 2), default=0)  # Новое поле: внутренний перевод
    dokidka_comment = db.Column(db.Text, default='')
    internal_transfer_comment = db.Column(db.Text, default='')
    # Файлы выгрузки
    bybit_file = db.Column(db.String(255), default=None)  # путь к файлу выгрузки Bybit
    htx_file = db.Column(db.String(255), default=None)    # путь к файлу выгрузки HTX
    bliss_file = db.Column(db.String(255), default=None)  # путь к файлу выгрузки Bliss
    # Фотографии
    start_photo = db.Column(db.String(255), default=None) # фото начала смены
    end_photo = db.Column(db.String(255), default=None)   # фото конца смены
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    bybit_requests = db.Column(db.Integer, default=0)
    htx_requests = db.Column(db.Integer, default=0)
    bliss_requests = db.Column(db.Integer, default=0)
    # Новые поля для дат сделок по площадкам
    bybit_first_trade = db.Column(db.String(100), default='')
    bybit_last_trade = db.Column(db.String(100), default='')
    htx_first_trade = db.Column(db.String(100), default='')
    htx_last_trade = db.Column(db.String(100), default='')
    bliss_first_trade = db.Column(db.String(100), default='')
    bliss_last_trade = db.Column(db.String(100), default='')
    gate_first_trade = db.Column(db.String(100), default='')
    gate_last_trade = db.Column(db.String(100), default='')
    appeal_amount = db.Column(db.Numeric(15, 2), default=0)
    appeal_comment = db.Column(db.Text, default='')
    appeal_deducted = db.Column(db.Boolean, default=False)  # Новое поле: вычитать ли аппеляцию из прибыли
    # Время начала и окончания смены по МСК
    shift_start_time = db.Column(db.DateTime, default=None)  # Время начала смены
    shift_end_time = db.Column(db.DateTime, default=None)    # Время окончания смены

class OrderDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    shift_report_id = db.Column(db.Integer, db.ForeignKey('shift_report.id'), nullable=False)
    order_id = db.Column(db.String(100), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    side = db.Column(db.String(10), nullable=False)  # 'buy' или 'sell'
    quantity = db.Column(db.Numeric(15, 8), nullable=False)
    price = db.Column(db.Numeric(15, 8), nullable=False)
    total_usdt = db.Column(db.Numeric(15, 2), nullable=False)
    fees_usdt = db.Column(db.Numeric(15, 2), default=0)
    status = db.Column(db.String(20), nullable=False)  # 'success', 'failed', 'pending'
    executed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class InitialBalance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(20), nullable=False)
    account_name = db.Column(db.String(100), nullable=False)
    balance = db.Column(db.Numeric(15, 2), nullable=False, default=0)

class AccountBalanceHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    account_name = db.Column(db.String(100), nullable=False)
    platform = db.Column(db.String(20), nullable=False)
    shift_date = db.Column(db.Date, nullable=False)
    shift_type = db.Column(db.String(20), nullable=False)
    balance = db.Column(db.Numeric(15, 2), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True)
    employee_name = db.Column(db.String(100), nullable=True)
    balance_type = db.Column(db.String(10), nullable=False, default='end')  # start или end

class Order(db.Model):
    """Модель для хранения ордеров от расширения Bybit"""
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(100), nullable=False, unique=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    platform = db.Column(db.String(20), nullable=False, default='bybit')
    account_name = db.Column(db.String(100), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    side = db.Column(db.String(10), nullable=False)  # 'buy' или 'sell'
    quantity = db.Column(db.Numeric(15, 8), nullable=False)
    price = db.Column(db.Numeric(15, 8), nullable=False)
    total_usdt = db.Column(db.Numeric(15, 2), nullable=False)
    fees_usdt = db.Column(db.Numeric(15, 2), default=0)
    status = db.Column(db.String(20), nullable=False)  # 'filled', 'canceled', 'pending', 'appealed'
    executed_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связь с сотрудником
    employee = db.relationship('Employee', backref='orders')

class EmployeeScamHistory(db.Model):
    """Модель для хранения истории скамов сотрудников"""
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    shift_report_id = db.Column(db.Integer, db.ForeignKey('shift_report.id'), nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    comment = db.Column(db.Text, default='')
    date = db.Column(db.Date, nullable=False)  # Дата отчета, в котором был скам
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связи с другими таблицами
    employee = db.relationship('Employee', backref='scam_history')
    shift_report = db.relationship('ShiftReport', backref='scam_history')

class SalarySettings(db.Model):
    """Модель для хранения настроек расчета зарплаты"""
    id = db.Column(db.Integer, primary_key=True)
    base_percent = db.Column(db.Integer, nullable=False, default=30)  # Базовый процент от прибыли
    min_requests_per_day = db.Column(db.Integer, nullable=False, default=50)  # Минимальное количество заявок в день
    bonus_percent = db.Column(db.Integer, nullable=False, default=5)  # Бонус за перевыполнение плана
    bonus_requests_threshold = db.Column(db.Integer, nullable=False, default=70)  # Порог заявок для получения бонуса
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# API Endpoints
@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

@app.route('/api/employees', methods=['GET'])
def get_employees():
    employees = Employee.query.all()
    return jsonify([
        {
            'id': e.id,
            'name': e.name,
            'telegram': e.telegram,
            'created_at': e.created_at,
            'salary_percent': e.salary_percent
        } for e in employees
    ])

@app.route('/api/employees', methods=['POST'])
def create_employee():
    """Создаёт нового сотрудника. Ожидает JSON с полями name и telegram."""
    try:
        # Валидация входных данных
        data = request.json
        if not data or not data.get('name') or not data.get('telegram'):
            return jsonify({'error': 'Необходимо указать имя и telegram'}), 400
        employee = Employee(
            name=data['name'],
            telegram=data['telegram']
        )
        db.session.add(employee)
        db.session.commit()
        return jsonify({'id': employee.id, 'message': 'Employee created successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка при создании сотрудника: {str(e)}'}), 500

@app.route('/api/employees/<int:employee_id>', methods=['DELETE'])
def delete_employee(employee_id):
    """Удаляет сотрудника по id. Требует пароль администратора в JSON."""
    try:
        data = request.get_json()
        if not validate_admin_password(data):
            return jsonify({'error': 'Неверный пароль'}), 403
        employee = db.session.get(Employee, employee_id)
        if not employee:
            return jsonify({'error': 'Сотрудник не найден'}), 404
        db.session.delete(employee)
        db.session.commit()
        return jsonify({'message': 'Сотрудник удален'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка при удалении сотрудника: {str(e)}'}), 500

@app.route('/api/employees/<int:employee_id>', methods=['PUT'])
def update_employee(employee_id):
    data = request.json
    emp = db.session.get(Employee, employee_id)
    if not emp:
        return jsonify({'error': 'Employee not found'}), 404
    if 'name' in data:
        emp.name = data['name']
    if 'telegram' in data:
        emp.telegram = data['telegram']
    if 'salary_percent' in data:
        try:
            emp.salary_percent = float(data['salary_percent'])
        except Exception:
            return jsonify({'error': 'Invalid salary_percent'}), 400
    db.session.commit()
    return jsonify({'message': 'Employee updated'})

@app.route('/api/accounts', methods=['GET'])
def get_accounts():
    accounts = Account.query.filter_by(is_active=True).all()
    return jsonify([{
        'id': a.id,
        'employee_id': a.employee_id,
        'platform': a.platform,
        'account_name': a.account_name
    } for a in accounts])

@app.route('/api/accounts', methods=['POST'])
def create_account():
    """Создаёт новый аккаунт. Ожидает JSON с platform и account_name."""
    try:
        # Валидация входных данных
        data = request.json
        if not data or not data.get('platform') or not data.get('account_name'):
            return jsonify({'error': 'Необходимо указать platform и account_name'}), 400
        account = Account(
            platform=data['platform'],
            account_name=data['account_name']
        )
        db.session.add(account)
        db.session.commit()
        return jsonify({'id': account.id, 'message': 'Account created successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка при создании аккаунта: {str(e)}'}), 500

@app.route('/api/accounts/<int:account_id>', methods=['DELETE'])
def delete_account(account_id):
    """Удаляет аккаунт по id. Требует пароль администратора в JSON."""
    try:
        data = request.get_json()
        if not validate_admin_password(data):
            return jsonify({'error': 'Неверный пароль'}), 403
        account = db.session.get(Account, account_id)
        if not account:
            return jsonify({'error': 'Аккаунт не найден'}), 404
        db.session.delete(account)
        db.session.commit()
        return jsonify({'message': 'Аккаунт удален'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка при удалении аккаунта: {str(e)}'}), 500

@app.route('/api/reports', methods=['GET'])
def get_reports():
    """Возвращает список всех сменных отчётов с фильтрами по дате и сотруднику."""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    employee_id = request.args.get('employee_id')
    
    query = ShiftReport.query
    
    if start_date:
        query = query.filter(ShiftReport.shift_date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(ShiftReport.shift_date <= datetime.strptime(end_date, '%Y-%m-%d').date())
    if employee_id:
        query = query.filter(ShiftReport.employee_id == int(employee_id))
    
    reports = query.all()
    return jsonify([{
        'id': r.id,
        'employee_id': r.employee_id,
        'shift_date': r.shift_date.isoformat(),
        'shift_type': r.shift_type,
        'total_requests': r.total_requests,
        'balances_json': r.balances_json,
        'scam_amount': float(r.scam_amount),
        'scam_comment': r.scam_comment,
        'scam_personal': r.scam_personal,
        'dokidka_amount': float(r.dokidka_amount),
        'dokidka_comment': r.dokidka_comment,
        'internal_transfer_amount': float(r.internal_transfer_amount),
        'internal_transfer_comment': r.internal_transfer_comment,
        'bybit_file': r.bybit_file,
        'htx_file': r.htx_file,
        'bliss_file': r.bliss_file,
        'start_photo': r.start_photo,
        'end_photo': r.end_photo,
        'bybit_requests': r.bybit_requests,
        'htx_requests': r.htx_requests,
        'bliss_requests': r.bliss_requests,
        'bybit_first_trade': r.bybit_first_trade,
        'bybit_last_trade': r.bybit_last_trade,
        'htx_first_trade': r.htx_first_trade,
        'htx_last_trade': r.htx_last_trade,
        'bliss_first_trade': r.bliss_first_trade,
        'bliss_last_trade': r.bliss_last_trade,
        'gate_first_trade': r.gate_first_trade,
        'gate_last_trade': r.gate_last_trade,
        'appeal_amount': float(getattr(r, 'appeal_amount', 0) or 0),
        'appeal_comment': getattr(r, 'appeal_comment', ''),
        'shift_start_time': r.shift_start_time.isoformat() if r.shift_start_time else None,
        'shift_end_time': r.shift_end_time.isoformat() if r.shift_end_time else None
    } for r in reports])

def parse_bool(value):
    """Преобразует строковое значение в булево"""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on')
    return bool(value)

def safe_float(value, default=0.0):
    """Безопасно преобразует значение в float, возвращая default если не удается"""
    if value is None or value == '':
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_int(value, default=0):
    """Безопасно преобразует значение в int, возвращая default если не удается"""
    if value is None or value == '':
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def save_report_file(file, platform, report_id):
    """Сохраняет файл выгрузки для отчета"""
    if not file or not file.filename:
        return None
        
    # Создаем безопасное имя файла
    filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    # Сохраняем файл
    file.save(file_path)
    
    # Обновляем отчет с путем к файлу
    report = ShiftReport.query.get(report_id)
    if report:
        if platform == 'bybit':
            report.bybit_file = filename
        elif platform == 'htx':
            report.htx_file = filename
        elif platform == 'bliss':
            report.bliss_file = filename
        db.session.commit()
    
    return file_path

@app.route('/api/reports', methods=['POST'])
def create_report():
    """Создаёт сменный отчёт. Ожидает JSON или multipart/form-data с основными полями смены и файлами."""
    try:
        # Валидация и обработка данных/файлов
        if request.content_type and request.content_type.startswith('multipart/form-data'):
            form = request.form
            files = request.files
            
            # Валидация обязательных полей
            required_fields = ['employee_id', 'shift_date', 'shift_type']
            for field in required_fields:
                if not form.get(field):
                    return jsonify({'error': f'Поле {field} обязательно для заполнения'}), 400
            
            # Сохраняем файлы выгрузок и фото с валидацией
            file_keys = ['bybit_file', 'htx_file', 'bliss_file', 'start_photo', 'end_photo']
            file_paths = {}
            
            for key in file_keys:
                if key in files and files[key].filename:
                    file = files[key]
                    if file and allowed_file(file.filename):
                        if not validate_file_size(file):
                            return jsonify({'error': f'Файл {file.filename} слишком большой (максимум 16MB)'}), 400
                        filename = secure_filename(file.filename)
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        filename = f"{timestamp}_{filename}"
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(file_path)
                        file_paths[key] = filename
                    else:
                        return jsonify({'error': f'Недопустимый тип файла: {file.filename}'}), 400
                else:
                    file_paths[key] = None

            # Валидация числовых полей с безопасным преобразованием
            try:
                bybit_requests = safe_int(form.get('bybit_requests', 0))
                htx_requests = safe_int(form.get('htx_requests', 0))
                bliss_requests = safe_int(form.get('bliss_requests', 0))
                if any(x < 0 for x in [bybit_requests, htx_requests, bliss_requests]):
                    return jsonify({'error': 'Количество заявок не может быть отрицательным'}), 400
            except Exception as e:
                return jsonify({'error': f'Ошибка валидации числовых полей: {str(e)}'}), 400

            # Валидация JSON балансов
            try:
                balances_json = form.get('balances_json', '{}')
                json.loads(balances_json)  # Проверяем корректность JSON
            except json.JSONDecodeError:
                return jsonify({'error': 'Неверный формат JSON балансов'}), 400

            total_requests = bybit_requests + htx_requests + bliss_requests

            report = ShiftReport(
                employee_id=safe_int(form['employee_id']),
                shift_date=datetime.strptime(form['shift_date'], '%Y-%m-%d').date(),
                shift_type=form['shift_type'],
                total_requests=total_requests,
                balances_json=balances_json,
                scam_amount=safe_float(form.get('scam_amount', 0)),
                scam_comment=form.get('scam_comment', ''),
                scam_personal=parse_bool(form.get('scam_personal', False)),
                dokidka_amount=safe_float(form.get('dokidka_amount', 0)),
                dokidka_comment=form.get('dokidka_comment', ''),
                internal_transfer_amount=safe_float(form.get('internal_transfer_amount', 0)),
                internal_transfer_comment=form.get('internal_transfer_comment', ''),
                bybit_file=file_paths['bybit_file'],
                htx_file=file_paths['htx_file'],
                bliss_file=file_paths['bliss_file'],
                start_photo=file_paths['start_photo'],
                end_photo=file_paths['end_photo'],
                bybit_requests=bybit_requests,
                htx_requests=htx_requests,
                bliss_requests=bliss_requests,
                bybit_first_trade=form.get('bybit_first_trade', ''),
                bybit_last_trade=form.get('bybit_last_trade', ''),
                htx_first_trade=form.get('htx_first_trade', ''),
                htx_last_trade=form.get('htx_last_trade', ''),
                bliss_first_trade=form.get('bliss_first_trade', ''),
                bliss_last_trade=form.get('bliss_last_trade', ''),
                gate_first_trade=form.get('gate_first_trade', ''),
                gate_last_trade=form.get('gate_last_trade', ''),
                appeal_amount=safe_float(form.get('appeal_amount', 0)),
                appeal_comment=form.get('appeal_comment', ''),
                shift_start_time=datetime.strptime(form['shift_start_time'], '%Y-%m-%dT%H:%M') if form.get('shift_start_time') else None,
                shift_end_time=datetime.strptime(form['shift_end_time'], '%Y-%m-%dT%H:%M') if form.get('shift_end_time') else None
            )
            db.session.add(report)
            db.session.commit()
            
            # Обрабатываем файлы выгрузок с автоматической проверкой времени
            files_data = {}
            if file_paths['bybit_file']:
                files_data['bybit'] = os.path.join(app.config['UPLOAD_FOLDER'], file_paths['bybit_file'])
            if file_paths['htx_file']:
                files_data['htx'] = os.path.join(app.config['UPLOAD_FOLDER'], file_paths['htx_file'])
            if file_paths['bliss_file']:
                files_data['bliss'] = os.path.join(app.config['UPLOAD_FOLDER'], file_paths['bliss_file'])
            
            # Обрабатываем файлы с проверкой времени
            if files_data and report.shift_start_time and report.shift_end_time:
                file_stats = process_shift_files(
                    report.id,
                    report.employee_id,
                    report.shift_start_time,
                    report.shift_end_time,
                    files_data
                )
                
                return jsonify({
                    'id': report.id, 
                    'message': 'Report created successfully',
                    'file_processing': file_stats
                })
            else:
                # Привязываем ордера к сотруднику на основе времени смены
                from utils import link_orders_to_employee
                linked_orders = link_orders_to_employee(db.session, report)

                return jsonify({
                    'id': report.id, 
                    'message': 'Report created successfully',
                    'linked_orders': linked_orders
                })
        
        elif request.content_type and request.content_type.startswith('application/json'):
            # Обработка JSON данных
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Отсутствуют данные в запросе'}), 400
            
            # Валидация обязательных полей
            required_fields = ['employee_id', 'shift_date', 'shift_type']
            for field in required_fields:
                if not data.get(field):
                    return jsonify({'error': f'Поле {field} обязательно для заполнения'}), 400
            
            # Валидация числовых полей с безопасным преобразованием
            try:
                bybit_requests = safe_int(data.get('bybit_requests', 0))
                htx_requests = safe_int(data.get('htx_requests', 0))
                bliss_requests = safe_int(data.get('bliss_requests', 0))
                if any(x < 0 for x in [bybit_requests, htx_requests, bliss_requests]):
                    return jsonify({'error': 'Количество заявок не может быть отрицательным'}), 400
            except Exception as e:
                return jsonify({'error': f'Ошибка валидации числовых полей: {str(e)}'}), 400

            # Валидация JSON балансов
            try:
                balances_json = data.get('balances_json', '{}')
                if isinstance(balances_json, dict):
                    balances_json = json.dumps(balances_json)
                json.loads(balances_json)  # Проверяем корректность JSON
            except json.JSONDecodeError:
                return jsonify({'error': 'Неверный формат JSON балансов'}), 400

            total_requests = bybit_requests + htx_requests + bliss_requests

            report = ShiftReport(
                employee_id=safe_int(data['employee_id']),
                shift_date=datetime.strptime(data['shift_date'], '%Y-%m-%d').date(),
                shift_type=data['shift_type'],
                total_requests=total_requests,
                balances_json=balances_json,
                scam_amount=safe_float(data.get('scam_amount', 0)),
                scam_comment=data.get('scam_comment', ''),
                scam_personal=parse_bool(data.get('scam_personal', False)),
                dokidka_amount=safe_float(data.get('dokidka_amount', 0)),
                dokidka_comment=data.get('dokidka_comment', ''),
                internal_transfer_amount=safe_float(data.get('internal_transfer_amount', 0)),
                internal_transfer_comment=data.get('internal_transfer_comment', ''),
                bybit_file=data.get('bybit_file'),
                htx_file=data.get('htx_file'),
                bliss_file=data.get('bliss_file'),
                start_photo=data.get('start_photo'),
                end_photo=data.get('end_photo'),
                bybit_requests=bybit_requests,
                htx_requests=htx_requests,
                bliss_requests=bliss_requests,
                bybit_first_trade=data.get('bybit_first_trade', ''),
                bybit_last_trade=data.get('bybit_last_trade', ''),
                htx_first_trade=data.get('htx_first_trade', ''),
                htx_last_trade=data.get('htx_last_trade', ''),
                bliss_first_trade=data.get('bliss_first_trade', ''),
                bliss_last_trade=data.get('bliss_last_trade', ''),
                gate_first_trade=data.get('gate_first_trade', ''),
                gate_last_trade=data.get('gate_last_trade', ''),
                appeal_amount=safe_float(data.get('appeal_amount', 0)),
                appeal_comment=data.get('appeal_comment', ''),
                shift_start_time=datetime.strptime(data['shift_start_time'], '%Y-%m-%dT%H:%M') if data.get('shift_start_time') else None,
                shift_end_time=datetime.strptime(data['shift_end_time'], '%Y-%m-%dT%H:%M') if data.get('shift_end_time') else None
            )
            db.session.add(report)
            db.session.commit()
            
            # Обрабатываем файлы выгрузок с автоматической проверкой времени
            files_data = {}
            if data.get('bybit_file'):
                files_data['bybit'] = data['bybit_file']
            if data.get('htx_file'):
                files_data['htx'] = data['htx_file']
            if data.get('bliss_file'):
                files_data['bliss'] = data['bliss_file']
            
            # Обрабатываем файлы с проверкой времени
            if files_data and report.shift_start_time and report.shift_end_time:
                file_stats = process_shift_files(
                    report.id,
                    report.employee_id,
                    report.shift_start_time,
                    report.shift_end_time,
                    files_data
                )
                
                return jsonify({
                    'id': report.id, 
                    'message': 'Report created successfully',
                    'file_processing': file_stats
                })
            else:
                # Привязываем ордера к сотруднику на основе времени смены
                from utils import link_orders_to_employee
                linked_orders = link_orders_to_employee(db.session, report)

                return jsonify({
                    'id': report.id, 
                    'message': 'Report created successfully',
                    'linked_orders': linked_orders
                })
        
        else:
            # Неподдерживаемый тип контента
            return jsonify({'error': 'Неподдерживаемый тип контента. Используйте multipart/form-data или application/json'}), 400
            
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка валидации данных: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Ошибка при создании отчета: {str(e)}')
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@app.route('/api/reports/<int:report_id>', methods=['DELETE'])
def delete_report(report_id):
    """Удаляет сменный отчёт по id. Требует пароль администратора в JSON."""
    try:
        data = request.get_json()
        if not validate_admin_password(data):
            return jsonify({'error': 'Неверный пароль'}), 403
        report = db.session.get(ShiftReport, report_id)
        if not report:
            return jsonify({'error': 'Отчет не найден'}), 404
        db.session.delete(report)
        db.session.commit()
        return jsonify({'message': 'Отчет удален'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка при удалении отчета: {str(e)}'}), 500

def calculate_employee_stats(reports, employees, db):
    """Вычисляет статистику по сотрудникам для дашборда (кол-во заявок, прибыль и т.д.)."""
    stats = []
    for emp in employees:
        emp_reports = [r for r in reports if r.employee_id == emp.id]
        emp_requests = sum((r.bybit_requests or 0) + (r.htx_requests or 0) + (r.bliss_requests or 0) for r in emp_reports)
        emp_profit = sum(calculate_report_profit(db.session, r)['profit'] for r in emp_reports)
        emp_shifts = len(emp_reports)
        avg_profit_per_shift = emp_profit / emp_shifts if emp_shifts else 0
        stats.append({
            'id': emp.id,
            'name': emp.name,
            'telegram': emp.telegram,
            'total_requests': emp_requests,
            'net_profit': round(emp_profit,2),
            'total_shifts': emp_shifts,
            'avg_profit_per_shift': round(avg_profit_per_shift,2)
        })
    return stats

def calculate_last_reports(db, last_reports_query):
    """Формирует список последних смен с расчетом прибыли и балансов по площадкам для дашборда."""
    last_reports = []
    for r in last_reports_query:
        profit_data = calculate_report_profit(db.session, r)
        try:
            balances = json.loads(r.balances_json or '{}')
        except json.JSONDecodeError:
            balances = {}
        emp = db.session.get(Employee, r.employee_id)
        employee_name = emp.name if emp else '—'
        platform_stats = {}
        for platform in ['bybit','htx','bliss','gate']:
            accounts_list = balances.get(platform, [])
            count = len(accounts_list)
            sum_delta = 0
            for acc in accounts_list:
                prev = find_prev_balance(db.session, acc.get('account_id') or acc.get('id'), platform, r)
                cur = float(acc.get('balance', 0)) if acc.get('balance') not in (None, '') else 0
                sum_delta += cur - prev
            platform_stats[platform] = {'count': count, 'delta': round(sum_delta,2)}
        profit = sum(platform_stats[p]['delta'] for p in platform_stats)
        scam = float(r.scam_amount or 0)
        transfer = float(r.dokidka_amount or 0)
        net_profit = profit - scam - transfer
        last_reports.append({
            'id': r.id,
            'employee_name': employee_name,
            'shift_date': r.shift_date.isoformat(),
            'shift_type': r.shift_type,
            'total_requests': r.total_requests,
            'profit': round(net_profit,2),
            'bybit_accounts': platform_stats['bybit']['count'],
            'bybit_delta': platform_stats['bybit']['delta'],
            'htx_accounts': platform_stats['htx']['count'],
            'htx_delta': platform_stats['htx']['delta'],
            'bliss_accounts': platform_stats['bliss']['count'],
            'bliss_delta': platform_stats['bliss']['delta'],
            'gate_accounts': platform_stats['gate']['count'],
            'gate_delta': platform_stats['gate']['delta'],
        })
    return last_reports

def calculate_account_balances(accounts, reports, db):
    """Вычисляет финальные балансы по всем аккаунтам для дашборда."""
    account_balances = {}
    for acc in accounts:
        account_balances[acc.id] = calculate_account_last_balance(db.session, acc.id, acc.platform, reports)
    return account_balances

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard_data():
    """Возвращает агрегированные данные для дашборда с поддержкой фильтрации по дате. Топ-3 сотрудников и общая прибыль всегда за текущий месяц."""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    if start_date and end_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    else:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
    reports = ShiftReport.query.filter(
        ShiftReport.shift_date >= start_date,
        ShiftReport.shift_date <= end_date
    ).all()
    # --- Общая прибыль за выбранный период (оставляем для других целей) ---
    total_profit = sum(calculate_report_profit(db.session, r)['salary_profit'] for r in reports)
    # --- Общий объем: сумма всех end_balance по всем аккаунтам на конец последней смены ---
    accounts = Account.query.filter_by(is_active=True).all()
    last_report = max(reports, key=lambda r: (r.shift_date, 0 if r.shift_type=='morning' else 1), default=None)
    total_volume = 0.0
    if last_report:
        try:
            balances = json.loads(last_report.balances_json or '{}')
        except:
            balances = {}
        for platform in ['bybit','htx','bliss','gate']:
            if balances.get(platform):
                for acc in balances[platform]:
                    end = float(acc.get('end_balance', 0) or 0)
                    total_volume += end
    total_requests = sum((r.bybit_requests or 0) + (r.htx_requests or 0) + (r.bliss_requests or 0) for r in reports)
    morning_profit = 0
    evening_profit = 0
    reports_with_net = []
    for r in reports:
        profit_data = calculate_report_profit(db.session, r)
        net_profit = profit_data['project_profit']
        if r.shift_type == 'morning':
            morning_profit += net_profit
        elif r.shift_type == 'evening':
            evening_profit += net_profit
        reports_with_net.append({
            'id': r.id,
            'employee_id': r.employee_id,
            'shift_date': r.shift_date.isoformat(),
            'shift_type': r.shift_type,
            'total_requests': r.total_requests,
            'balances_json': r.balances_json,
            'scam_amount': float(r.scam_amount),
            'scam_comment': r.scam_comment,
            'scam_personal': r.scam_personal,
            'dokidka_amount': float(r.dokidka_amount),
            'dokidka_comment': r.dokidka_comment,
            'internal_transfer_amount': float(r.internal_transfer_amount),
            'internal_transfer_comment': r.internal_transfer_comment,
            'bybit_file': r.bybit_file,
            'htx_file': r.htx_file,
            'bliss_file': r.bliss_file,
            'start_photo': r.start_photo,
            'end_photo': r.end_photo,
            'bybit_requests': r.bybit_requests,
            'htx_requests': r.htx_requests,
            'bliss_requests': r.bliss_requests,
            'net_profit': round(net_profit, 2)
        })
    # --- Статистика по сотрудникам (ТОП-3) и общая прибыль всегда за текущий календарный месяц ---
    today = datetime.now().date()
    month_start = today.replace(day=1)
    month_end = (today.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    month_reports = ShiftReport.query.filter(
        ShiftReport.shift_date >= month_start,
        ShiftReport.shift_date <= month_end
    ).all()
    employees = Employee.query.filter_by(is_active=True).all()
    employee_stats = calculate_employee_stats(month_reports, employees, db)
    month_total_profit = sum(calculate_report_profit(db.session, r)['profit'] for r in month_reports)
    month_total_requests = sum((r.bybit_requests or 0) + (r.htx_requests or 0) + (r.bliss_requests or 0) for r in month_reports)
    # --- LAST REPORTS (3 последних смены) ---
    last_reports_query = ShiftReport.query.order_by(ShiftReport.shift_date.desc(), ShiftReport.created_at.desc()).limit(3).all()
    last_reports = calculate_last_reports(db, last_reports_query)
    dashboard = {
        'total_profit': round(total_profit,2),
        'month_total_profit': round(month_total_profit,2),
        'total_volume': round(total_volume,2),
        'total_requests': total_requests,
        'month_total_requests': month_total_requests,
        'morning_profit': round(morning_profit,2),
        'evening_profit': round(evening_profit,2),
        'employee_stats': employee_stats,
        'last_reports': last_reports,
        'reports': reports_with_net,
        'profit_by_day': group_reports_by_day_net_profit(reports_with_net)
    }
    return jsonify(dashboard)

@app.route('/api/settings/balances', methods=['GET', 'POST'])
def settings_balances():
    """Получение и сохранение начальных балансов. POST требует пароль администратора."""
    if request.method == 'GET':
        # Возвращаем все начальные балансы
        balances = InitialBalance.query.all()
        return jsonify([
            {'id': b.id, 'platform': b.platform, 'account_name': b.account_name, 'balance': float(b.balance)}
            for b in balances
        ])
    elif request.method == 'POST':
        try:
            data = request.json
            if not validate_admin_password(data):
                return jsonify({'error': 'Неверный пароль'}), 403
            # Ожидаем список балансов: [{platform, account_name, balance}]
            if not data.get('balances') or not isinstance(data['balances'], list):
                return jsonify({'error': 'Необходимо передать список balances'}), 400
            InitialBalance.query.delete()
            for item in data.get('balances', []):
                if not item.get('platform') or not item.get('account_name'):
                    return jsonify({'error': 'Каждый баланс должен содержать platform и account_name'}), 400
                b = InitialBalance(
                    platform=item['platform'],
                    account_name=item['account_name'],
                    balance=item['balance']
                )
                db.session.add(b)
            db.session.commit()
            return jsonify({'message': 'Начальные балансы сохранены'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Ошибка при сохранении балансов: {str(e)}'}), 500

def calculate_employee_statistics(reports, emp, db):
    """Вычисляет подробную статистику по одному сотруднику для /api/statistics (смены, заявки, прибыль, скам, переводы, зарплата и т.д.)."""
    if not reports:
        return {
            'id': emp.id,
            'name': emp.name,
            'telegram': emp.telegram,
            'total_days': 0,
            'total_shifts': 0,
            'total_requests': 0,
            'avg_requests_per_day': 0,
            'total_profit': 0,
            'net_profit': 0,
            'salary': 0,
            'total_scam': 0,
            'total_transfer': 0,
            'avg_profit_per_shift': 0,
            'total_bybit': 0,
            'total_htx': 0,
            'total_bliss': 0
        }
    # Используем total_requests если есть, иначе сумму по платформам
    total_requests_from_platforms = sum((r.bybit_requests or 0) + (r.htx_requests or 0) + (r.bliss_requests or 0) for r in reports)
    total_requests_from_field = sum(r.total_requests or 0 for r in reports)
    total_requests = max(total_requests_from_platforms, total_requests_from_field)
    
    total_bybit = sum(r.bybit_requests or 0 for r in reports)
    total_htx = sum(r.htx_requests or 0 for r in reports)
    total_bliss = sum(r.bliss_requests or 0 for r in reports)
    # Считаем только скамы по вине сотрудника
    total_scam = float(sum(r.scam_amount or 0 for r in reports if getattr(r, 'scam_personal', False)))
    total_transfer = float(sum(r.dokidka_amount or 0 for r in reports))
    # Считаем прибыль по новой логике
    total_project_profit = sum(calculate_report_profit(db.session, r)['project_profit'] for r in reports)
    total_salary_profit = sum(calculate_report_profit(db.session, r)['salary_profit'] for r in reports)
    # Используем индивидуальный процент сотрудника, если задан, иначе 30%
    salary_percent = emp.salary_percent if emp.salary_percent is not None else 30.0
    salary = max(0, total_salary_profit * (salary_percent / 100))
    total_shifts = len(reports)
    total_days = len(set(r.shift_date for r in reports))
    avg_requests_per_day = total_requests / total_days if total_days else 0
    avg_profit_per_shift = total_salary_profit / total_shifts if total_shifts else 0
    return {
        'id': emp.id,
        'name': emp.name,
        'telegram': emp.telegram,
        'total_days': total_days,
        'total_shifts': total_shifts,
        'total_requests': total_requests,
        'total_bybit': total_bybit,
        'total_htx': total_htx,
        'total_bliss': total_bliss,
        'avg_requests_per_day': round(avg_requests_per_day,2),
        'total_profit': round(total_project_profit,2),
        'net_profit': round(total_salary_profit,2),
        'salary': round(salary,2),
        'total_scam': round(total_scam,2),
        'total_transfer': round(total_transfer,2),
        'avg_profit_per_shift': round(avg_profit_per_shift,2)
    }

@app.route('/api/statistics', methods=['GET'])
def statistics():
    """Возвращает подробную статистику по сотрудникам за выбранный период: смены, заявки, прибыль, скам, переводы, зарплата и т.д."""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    if not start_date or not end_date:
        today = datetime.now().date()
        start_date = today.replace(day=1)
        end_date = today
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    employees = Employee.query.filter_by(is_active=True).all()
    stats = []
    for emp in employees:
        reports = ShiftReport.query.filter(
            ShiftReport.employee_id == emp.id,
            ShiftReport.shift_date >= start_date,
            ShiftReport.shift_date <= end_date
        ).all()
        stats.append(calculate_employee_statistics(reports, emp, db))
    return jsonify(stats)

@app.route('/logout')
def logout():
    """Endpoint для выхода из системы"""
    # В данном случае просто перенаправляем на главную страницу
    # В реальном приложении здесь можно добавить очистку сессии
    return jsonify({'message': 'Выход выполнен успешно', 'redirect': '/'})

@app.route('/api/account-balance-history', methods=['GET'])
def get_account_balance_history():
    """Возвращает историю балансов аккаунтов с фильтрами."""
    query = AccountBalanceHistory.query
    account_id = request.args.get('account_id')
    platform = request.args.get('platform')
    employee_id = request.args.get('employee_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    if account_id:
        query = query.filter(AccountBalanceHistory.account_id == int(account_id))
    if platform:
        query = query.filter(AccountBalanceHistory.platform == platform)
    if employee_id:
        query = query.filter(AccountBalanceHistory.employee_id == int(employee_id))
    if start_date:
        query = query.filter(AccountBalanceHistory.shift_date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(AccountBalanceHistory.shift_date <= datetime.strptime(end_date, '%Y-%m-%d').date())
    history = query.order_by(AccountBalanceHistory.shift_date, AccountBalanceHistory.shift_type).all()
    return jsonify([
        {
            'id': h.id,
            'account_id': h.account_id,
            'account_name': h.account_name,
            'platform': h.platform,
            'shift_date': h.shift_date.isoformat(),
            'shift_type': h.shift_type,
            'balance': float(h.balance),
            'employee_id': h.employee_id,
            'employee_name': h.employee_name,
            'balance_type': h.balance_type
        }
        for h in history
    ])

@app.route('/api/account-balance-history', methods=['POST'])
def add_account_balance_history():
    """Добавляет запись в историю балансов аккаунтов."""
    try:
        data = request.json
        if not data or not data.get('account_id') or not data.get('platform') or not data.get('shift_date') or not data.get('shift_type'):
            return jsonify({'error': 'Необходимо указать account_id, platform, shift_date, shift_type'}), 400
        history = AccountBalanceHistory(
            account_id=data['account_id'],
            account_name=data.get('account_name', ''),
            platform=data['platform'],
            shift_date=datetime.strptime(data['shift_date'], '%Y-%m-%d').date(),
            shift_type=data['shift_type'],
            balance=data.get('balance', 0),
            employee_id=data.get('employee_id'),
            employee_name=data.get('employee_name', ''),
            balance_type=data.get('balance_type', 'end')
        )
        db.session.add(history)
        db.session.commit()
        return jsonify({'id': history.id, 'message': 'Account balance history added'})
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка валидации данных: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Ошибка при добавлении в историю балансов: {str(e)}')
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

# Добавляю новые API endpoints для безопасной аутентификации
@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """API endpoint для аутентификации пользователей"""
    try:
        data = request.json
        if not data or not data.get('password'):
            return jsonify({'error': 'Пароль обязателен'}), 400
        
        # Проверяем пароль приложения
        app_password = os.environ.get('APP_PASSWORD', '7605203')
        if data['password'] == app_password:
            return jsonify({'success': True, 'message': 'Аутентификация успешна'})
        else:
            return jsonify({'error': 'Неверный пароль'}), 401
    except Exception as e:
        app.logger.error(f'Ошибка аутентификации: {str(e)}')
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@app.route('/api/auth/admin', methods=['POST'])
def api_admin_login():
    """API endpoint для аутентификации администратора"""
    try:
        data = request.json
        if not data or not data.get('password'):
            return jsonify({'error': 'Пароль обязателен'}), 400
        
        # Проверяем пароль администратора
        admin_password = os.environ.get('ADMIN_PASSWORD', 'Blalala2')
        if data['password'] == admin_password:
            return jsonify({'success': True, 'message': 'Аутентификация администратора успешна'})
        else:
            return jsonify({'error': 'Неверный пароль администратора'}), 401
    except Exception as e:
        app.logger.error(f'Ошибка аутентификации администратора: {str(e)}')
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@app.route('/api/orders', methods=['GET'])
def get_orders():
    """Возвращает список ордеров с фильтрами"""
    employee_id = request.args.get('employee_id')
    platform = request.args.get('platform')
    status = request.args.get('status')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = Order.query
    
    if employee_id:
        query = query.filter(Order.employee_id == int(employee_id))
    if platform:
        query = query.filter(Order.platform == platform)
    if status:
        query = query.filter(Order.status == status)
    if start_date:
        query = query.filter(Order.executed_at >= datetime.strptime(start_date, '%Y-%m-%d'))
    if end_date:
        # Добавляем один день к end_date и используем строгое сравнение для включения всего дня
        end_date_plus_one = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        query = query.filter(Order.executed_at < end_date_plus_one)
    
    # Сортировка по дате выполнения (новые сначала)
    query = query.order_by(Order.executed_at.desc())
    
    orders = query.all()
    
    return jsonify([{
        'id': o.id,
        'order_id': o.order_id,
        'employee_id': o.employee_id,
        'employee_name': o.employee.name if o.employee else '',
        'platform': o.platform,
        'account_name': o.account_name,
        'symbol': o.symbol,
        'side': o.side,
        'quantity': float(o.quantity),
        'price': float(o.price),
        'total_usdt': float(o.total_usdt),
        'fees_usdt': float(o.fees_usdt),
        'status': o.status,
        'executed_at': o.executed_at.isoformat(),
        'created_at': o.created_at.isoformat()
    } for o in orders])

@app.route('/api/orders', methods=['POST'])
def create_order():
    """Создает новый ордер от расширения Bybit"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Нет данных'}), 400
        
        # Валидация обязательных полей
        required_fields = ['order_id', 'employee_id', 'symbol', 'side', 'quantity', 'price']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Отсутствует обязательное поле: {field}'}), 400
        
        # Проверяем, что сотрудник существует
        employee = db.session.get(Employee, data['employee_id'])
        if not employee:
            return jsonify({'error': 'Сотрудник не найден'}), 404
        
        # Проверяем, что ордер еще не существует
        existing_order = Order.query.filter_by(order_id=data['order_id']).first()
        if existing_order:
            return jsonify({'error': 'Ордер уже существует'}), 409
        
        # Создаем ордер с данными пользователя как есть (без автовычислений)
        order = Order(
            order_id=data['order_id'],
            employee_id=data['employee_id'],
            platform=data.get('platform', 'bybit'),
            account_name=data.get('account_name', ''),
            symbol=data['symbol'],
            side=data['side'],
            quantity=data['quantity'],
            price=data['price'],
            total_usdt=data['total_usdt'],  # Используем значение, введенное пользователем
            fees_usdt=data.get('fees_usdt', 0),
            status=data.get('status', 'filled'),
            executed_at=datetime.fromisoformat(data['executed_at']) if data.get('executed_at') else datetime.utcnow()
        )
        
        db.session.add(order)
        db.session.commit()
        
        return jsonify({
            'id': order.id,
            'message': 'Ордер успешно создан'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка создания ордера: {str(e)}'}), 500

@app.route('/api/orders/<int:order_id>', methods=['PUT'])
def update_order(order_id):
    """Обновляет статус ордера"""
    try:
        data = request.json
        order = db.session.get(Order, order_id)
        
        if not order:
            return jsonify({'error': 'Ордер не найден'}), 404
        
        # Обновляем только разрешенные поля
        if 'status' in data:
            order.status = data['status']
        if 'fees_usdt' in data:
            order.fees_usdt = data['fees_usdt']
        
        db.session.commit()
        
        return jsonify({'message': 'Ордер обновлен'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка обновления ордера: {str(e)}'}), 500

@app.route('/api/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    """Удаляет ордер"""
    try:
        data = request.get_json()
        if not validate_admin_password(data):
            return jsonify({'error': 'Неверный пароль'}), 403
        
        order = db.session.get(Order, order_id)
        if not order:
            return jsonify({'error': 'Ордер не найден'}), 404
        
        db.session.delete(order)
        db.session.commit()
        
        return jsonify({'message': 'Ордер удален'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка удаления ордера: {str(e)}'}), 500

@app.route('/api/orders/bulk-delete', methods=['POST'])
def bulk_delete_orders():
    """Массовое удаление ордеров"""
    try:
        data = request.get_json()
        order_ids = data.get('order_ids', [])
        
        if not order_ids:
            return jsonify({'error': 'Не указаны ID ордеров для удаления'}), 400
        
        # Находим все ордеры для удаления
        orders_to_delete = Order.query.filter(Order.id.in_(order_ids)).all()
        
        if not orders_to_delete:
            return jsonify({'error': 'Ордеры не найдены'}), 404
        
        # Удаляем ордеры
        for order in orders_to_delete:
            db.session.delete(order)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'deleted_count': len(orders_to_delete),
            'message': f'Успешно удалено {len(orders_to_delete)} ордеров'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка при массовом удалении: {str(e)}'}), 500

@app.route('/api/orders/statistics', methods=['GET'])
def get_orders_statistics():
    """Возвращает статистику по ордерам"""
    employee_id = request.args.get('employee_id')
    platform = request.args.get('platform')
    status = request.args.get('status')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    exclude_canceled = request.args.get('exclude_canceled', 'true').lower() == 'true'  # По умолчанию исключаем отмененные
    
    query = Order.query
    
    if employee_id:
        query = query.filter(Order.employee_id == int(employee_id))
    if platform:
        query = query.filter(Order.platform == platform)
    if status:
        query = query.filter(Order.status == status)
    elif exclude_canceled:
        # Если статус не указан явно, исключаем отмененные и неуспешные ордера
        query = query.filter(~Order.status.in_(['canceled', 'expired', 'failed']))
    if start_date:
        query = query.filter(Order.executed_at >= datetime.strptime(start_date, '%Y-%m-%d'))
    if end_date:
        # Добавляем один день к end_date и используем строгое сравнение для включения всего дня
        end_date_plus_one = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        query = query.filter(Order.executed_at < end_date_plus_one)
    
    orders = query.all()
    
    # Статистика
    total_orders = len(orders)
    total_volume = sum(float(o.total_usdt) for o in orders)  # Общий объем RUB
    total_quantity = sum(float(o.quantity) for o in orders)  # Общий объем USDT
    total_fees = sum(float(o.fees_usdt) for o in orders)
    
    # Статистика по статусам
    status_stats = {}
    for order in orders:
        status = order.status
        if status not in status_stats:
            status_stats[status] = 0
        status_stats[status] += 1
    
    # Статистика по сторонам (buy/sell) - используем только завершенные ордера
    completed_orders = [o for o in orders if o.status == 'filled']
    buy_orders = [o for o in completed_orders if o.side == 'buy']
    sell_orders = [o for o in completed_orders if o.side == 'sell']
    
    # Расчет объемов только для завершенных ордеров
    buy_volume_rub = sum(float(o.total_usdt) for o in buy_orders)    # Сумма RUB для покупок
    sell_volume_rub = sum(float(o.total_usdt) for o in sell_orders)  # Сумма RUB для продаж
    buy_volume_usdt = sum(float(o.quantity) for o in buy_orders)     # Сумма USDT для покупок
    sell_volume_usdt = sum(float(o.quantity) for o in sell_orders)   # Сумма USDT для продаж
    
    # Расчет среднего курса для завершенных ордеров
    avg_buy_rate = buy_volume_rub / buy_volume_usdt if buy_volume_usdt > 0 else 0
    avg_sell_rate = sell_volume_rub / sell_volume_usdt if sell_volume_usdt > 0 else 0
    
    # Рассчитываем прибыль в USDT (покупки - продажи)
    profit_usdt = buy_volume_usdt - sell_volume_usdt
    
    # Получаем значения докидки, внутреннего перевода и скама
    dokidka_amount = float(request.args.get('dokidka_amount', 0) or 0)
    internal_transfer_amount = float(request.args.get('internal_transfer_amount', 0) or 0)
    scam_amount = float(request.args.get('scam_amount', 0) or 0)
    
    # Вычитаем из прибыли
    profit_usdt = profit_usdt - dokidka_amount - internal_transfer_amount - scam_amount

    return jsonify({
        'total_orders': total_orders,
        'status_stats': status_stats,
        'sell_volume': round(sell_volume_rub, 2),
        'buy_volume': round(buy_volume_rub, 2),
        'sell_volume_usdt': round(sell_volume_usdt, 2),
        'buy_volume_usdt': round(buy_volume_usdt, 2),
        'avg_sell_rate': round(avg_sell_rate, 2),
        'avg_buy_rate': round(avg_buy_rate, 2),
        'profit_usdt': round(profit_usdt, 2)
    })

@app.route('/api/orders/upload', methods=['POST'])
def upload_orders():
    """Загружает ордера из файла Excel/CSV с фильтрацией по времени"""
    try:
        # Проверяем обязательные поля
        employee_id = request.form.get('employee_id')
        platform = request.form.get('platform')
        account_name = request.form.get('account_name')
        
        if not employee_id or not platform or not account_name:
            return jsonify({'error': 'Не указаны обязательные поля'}), 400
        
        # Получаем параметры фильтрации по времени
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        
        print(f"\nDEBUG UPLOAD: Параметры запроса:")
        print(f"DEBUG UPLOAD: employee_id = {employee_id}")
        print(f"DEBUG UPLOAD: platform = {platform}")
        print(f"DEBUG UPLOAD: account_name = {account_name}")
        print(f"DEBUG UPLOAD: start_date_str = {start_date_str}")
        print(f"DEBUG UPLOAD: end_date_str = {end_date_str}")
        
        start_date = None
        end_date = None
        
        # Парсим начальную дату
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M')
                print(f"DEBUG UPLOAD: start_date = {start_date}")
            except ValueError:
                return jsonify({'error': 'Неверный формат начальной даты'}), 400
        
        # Парсим конечную дату
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%dT%H:%M')
                print(f"DEBUG UPLOAD: end_date = {end_date}")
            except ValueError:
                return jsonify({'error': 'Неверный формат конечной даты'}), 400
        
        # Проверяем логику дат
        if start_date and end_date and start_date > end_date:
            return jsonify({'error': 'Начальная дата не может быть больше конечной'}), 400
        
        # Проверяем, что сотрудник существует
        employee = db.session.get(Employee, employee_id)
        if not employee:
            return jsonify({'error': 'Сотрудник не найден'}), 404
        
        # Проверяем файл
        if 'file' not in request.files:
            return jsonify({'error': 'Файл не загружен'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Файл не выбран'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Неподдерживаемый тип файла'}), 400
        
        # Сохраняем файл с правильным расширением
        original_filename = file.filename or 'upload.xlsx'
        # Определяем расширение из оригинального имени файла
        file_ext = os.path.splitext(original_filename)[1].lower()
        if not file_ext:
            file_ext = '.xlsx'  # По умолчанию
        
        # Создаем безопасное имя файла, сохраняя расширение
        safe_name = secure_filename(original_filename)
        if not safe_name or len(safe_name) < 3:
            safe_name = f"upload{file_ext}"
        else:
            # Если secure_filename удалил все символы кроме расширения, добавляем имя по умолчанию
            base_name = os.path.splitext(safe_name)[0]
            if not base_name or len(base_name) < 1:
                safe_name = f"upload{file_ext}"
            elif not safe_name.endswith(file_ext):
                # Если расширение потерялось, добавляем его
                safe_name = f"{base_name}{file_ext}"
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{safe_name}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        print(f"DEBUG UPLOAD: Сохраняем файл: {filepath}")
        file.save(filepath)
        
        # Обрабатываем файл с фильтрацией по времени, передаем оригинальное имя для определения типа
        orders_data = parse_orders_file(filepath, platform, start_date, end_date, original_filename)
        print(f"DEBUG UPLOAD: Получено {len(orders_data)} ордеров из файла")
        
        # Сохраняем ордера в базу данных
        created_orders = []
        skipped_orders = []
        
        for order_data in orders_data:
            # Проверяем, что ордер еще не существует
            existing_order = Order.query.filter_by(
                order_id=order_data['order_id'],
                platform=platform
            ).first()
            if existing_order:
                skipped_orders.append(order_data['order_id'])
                continue
            
            # Создаем новый ордер
            order = Order(
                order_id=order_data['order_id'],
                employee_id=employee_id,
                platform=platform,
                account_name=order_data.get('account_name') or account_name,  # Используем account_name из order_data, если есть
                symbol=order_data['symbol'],
                side=order_data['side'],
                quantity=order_data['quantity'],
                price=order_data['price'],
                total_usdt=order_data['total_usdt'],
                fees_usdt=order_data.get('fees_usdt', 0),
                status=order_data.get('status', 'filled'),
                executed_at=order_data['executed_at']
            )
            
            db.session.add(order)
            created_orders.append(order_data['order_id'])
            print(f"DEBUG UPLOAD: Создан ордер {order_data['order_id']}")
        
        db.session.commit()
        
        # Формируем сообщение о результате
        message = f'Загружено {len(created_orders)} ордеров, пропущено {len(skipped_orders)} дублей'
        if start_date or end_date:
            total_parsed = len(orders_data)
            message += f', обработано {total_parsed} ордеров из файла'
            if start_date:
                message += f' с {start_date.strftime("%d.%m.%Y %H:%M")}'
            if end_date:
                message += f' по {end_date.strftime("%d.%m.%Y %H:%M")}'
        
        return jsonify({
            'success': True,
            'count': len(created_orders),
            'skipped': len(skipped_orders),
            'total_parsed': len(orders_data),
            'message': message
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка обработки файла: {str(e)}'}), 500

@app.route('/api/platform-balances', methods=['GET'])
def get_platform_balances():
    """Возвращает текущие балансы по всем площадкам"""
    try:
        # Получаем все отчеты, отсортированные по дате и ID
        all_reports = ShiftReport.query.order_by(
            ShiftReport.shift_date.desc(), 
            ShiftReport.id.desc()
        ).all()
        
        if not all_reports:
            return jsonify({
                'platforms': [],
                'total_balance': 0,
                'active_platforms_count': 0,
                'last_update': None,
                'message': 'Нет данных о балансах'
            })
        
        # Собираем последние балансы для каждого аккаунта
        account_balances = {}  # {platform: {account_name: {balance, last_update_info}}}
        
        for report in all_reports:
            try:
                balances = json.loads(report.balances_json or '{}')
            except json.JSONDecodeError:
                continue
                
            employee = db.session.get(Employee, report.employee_id)
            employee_name = employee.name if employee else 'Неизвестный сотрудник'
            
            for platform in ['bybit', 'htx', 'bliss', 'gate']:
                if platform not in account_balances:
                    account_balances[platform] = {}
                    
                platform_accounts = balances.get(platform, [])
                for acc in platform_accounts:
                    account_name = acc.get('account_name', 'Неизвестный аккаунт')
                    
                    # Если для этого аккаунта ещё нет записи, добавляем её
                    if account_name not in account_balances[platform]:
                        try:
                            balance_str = acc.get('end_balance', '0')
                            balance = float(balance_str) if balance_str and balance_str != '' else 0.0
                        except (ValueError, TypeError):
                            balance = 0.0
                            
                        account_balances[platform][account_name] = {
                            'balance': balance,
                            'account_id': acc.get('account_id') or acc.get('id'),
                            'last_update': {
                                'date': report.shift_date.isoformat(),
                                'shift_type': report.shift_type,
                                'employee_name': employee_name
                            }
                        }
        
        # Формируем результат
        platform_stats = []
        total_balance = 0
        active_platforms_count = 0
        latest_update = None
        
        for platform in ['bybit', 'htx', 'bliss', 'gate']:
            platform_accounts = account_balances.get(platform, {})
            platform_total = 0
            accounts_data = []
            
            for account_name, account_info in platform_accounts.items():
                balance = account_info['balance']
                platform_total += balance
                accounts_data.append({
                    'account_id': account_info['account_id'],
                    'account_name': account_name,
                    'balance': round(balance, 2),
                    'last_update': account_info['last_update']
                })
            
            total_balance += platform_total
            
            # Считаем площадку активной, если у неё есть аккаунты
            if len(platform_accounts) > 0:
                active_platforms_count += 1
            
            platform_stats.append({
                'platform': platform,
                'platform_name': {
                    'bybit': 'Bybit',
                    'htx': 'HTX',
                    'bliss': 'Bliss',
                    'gate': 'Gate'
                }.get(platform, platform.upper()),
                'total_balance': round(platform_total, 2),
                'accounts_count': len(platform_accounts),
                'accounts': accounts_data
            })
        
        # Информация о последнем обновлении (из самого свежего отчета)
        latest_report = all_reports[0]
        latest_employee = db.session.get(Employee, latest_report.employee_id)
        
        return jsonify({
            'platforms': platform_stats,
            'total_balance': round(total_balance, 2),
            'active_platforms_count': active_platforms_count,
            'last_update': {
                'date': latest_report.shift_date.isoformat(),
                'shift_type': latest_report.shift_type,
                'employee_name': latest_employee.name if latest_employee else 'Неизвестный сотрудник',
                'updated_at': latest_report.updated_at.isoformat() if latest_report.updated_at else None
            }
        })
        
    except Exception as e:
        app.logger.error(f'Ошибка при получении балансов площадок: {str(e)}')
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@app.route('/api/employee-profile/<int:employee_id>', methods=['GET'])
def get_employee_profile(employee_id):
    """Возвращает детальный профиль сотрудника с максимальным количеством показателей"""
    try:
        # Получаем параметры фильтрации
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            today = datetime.now().date()
            start_date = today.replace(day=1)
            end_date = today
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        print(f"🔍 Ищем отчеты за период: {start_date} - {end_date}")
        
        # Получаем сотрудника
        employee = Employee.query.get_or_404(employee_id)
        
        # Сначала проверим все отчеты этого сотрудника
        all_reports = ShiftReport.query.filter(
            ShiftReport.employee_id == employee_id
        ).order_by(ShiftReport.shift_date.desc()).all()
        
        # Получаем все отчеты сотрудника за период
        reports = ShiftReport.query.filter(
            ShiftReport.employee_id == employee_id,
            ShiftReport.shift_date >= start_date,
            ShiftReport.shift_date <= end_date
        ).order_by(ShiftReport.shift_date.desc()).all()
        
        # Отладочная информация
        print(f"🔍 Профиль сотрудника {employee.name} (ID: {employee_id})")
        print(f"📅 Период: {start_date} - {end_date}")
        print(f"📊 Всего отчетов у сотрудника: {len(all_reports)}")
        if all_reports:
            print("📋 Все отчеты сотрудника:")
            for r in all_reports:
                print(f"   - {r.shift_date} ({r.shift_type}) - {r.total_requests} заявок")
        print(f"📊 Найдено отчетов за период: {len(reports)}")
        for i, report in enumerate(reports):
            print(f"  📋 Отчет {i+1}: {report.shift_date} ({report.shift_type})")
            print(f"    Всего заявок: {report.total_requests}")
            print(f"    Bybit: {report.bybit_requests}, HTX: {report.htx_requests}, Bliss: {report.bliss_requests}")
            print(f"    Балансы JSON: {report.balances_json[:100]}...")
            profit_data = calculate_report_profit(db.session, report)
            print(f"    Прибыль: {profit_data}")
            print(f"    Скам: {report.scam_amount}, Докидка: {report.dokidka_amount}")
            print("    ---")
        
        # Автоматически привязываем ордера к отчетам сотрудника
        from utils import link_orders_to_employee
        total_linked = 0
        for report in reports:
            if report.shift_start_time and report.shift_end_time:
                linked_count = link_orders_to_employee(db.session, report)
                total_linked += linked_count
                if linked_count > 0:
                    print(f"🔗 Привязано {linked_count} ордеров к отчету от {report.shift_date}")
        
        if total_linked > 0:
            print(f"🔗 Всего привязано {total_linked} ордеров к отчетам сотрудника")
        
        # Получаем все ордера сотрудника за период
        orders = Order.query.filter(
            Order.employee_id == employee_id,
            Order.executed_at >= datetime.combine(start_date, datetime.min.time()),
            Order.executed_at < datetime.combine(end_date + timedelta(days=1), datetime.min.time())
        ).all()
        
        print("🔧 Начинаем расчет основной статистики...")
        try:
            # Основная статистика
            basic_stats = calculate_employee_statistics(reports, employee, db)
            print(f"✅ Основная статистика: {basic_stats}")
        except Exception as e:
            print(f"❌ Ошибка при расчете основной статистики: {str(e)}")
            import traceback
            traceback.print_exc()
            basic_stats = {}
        
        print("🔧 Начинаем расчет детальной статистики по отчетам...")
        # Детальная статистика по отчетам
        report_details = []
        total_project_profit = 0
        total_salary_profit = 0
        platform_profits = {'bybit': 0, 'htx': 0, 'bliss': 0, 'gate': 0}
        
        for i, report in enumerate(reports):
            print(f"🔧 Обрабатываем отчет {i+1}/{len(reports)}: {report.shift_date}")
            try:
                profit_data = calculate_report_profit(db.session, report)
                print(f"✅ Прибыль рассчитана: {profit_data}")
                total_project_profit += profit_data['project_profit']
                total_salary_profit += profit_data['salary_profit']
            except Exception as e:
                print(f"❌ Ошибка при расчете прибыли для отчета {report.shift_date}: {str(e)}")
                import traceback
                traceback.print_exc()
                profit_data = {'project_profit': 0, 'salary_profit': 0, 'profit': 0, 'scam': 0, 'dokidka': 0, 'internal': 0}
            
            # Парсим балансы
            print(f"🔧 Парсим балансы для отчета {report.shift_date}...")
            try:
                balances = json.loads(report.balances_json or '{}')
                print(f"✅ Балансы распарсены: {len(balances)} платформ")
            except Exception as e:
                print(f"❌ Ошибка при парсинге балансов: {str(e)}")
                balances = {}
            
            # Считаем прибыль по платформам
            print(f"🔧 Считаем прибыль по платформам...")
            platform_deltas = {}
            try:
                for platform in ['bybit', 'htx', 'bliss', 'gate']:
                    accounts_list = balances.get(platform, [])
                    delta = 0
                    for acc in accounts_list:
                        prev = find_prev_balance(db.session, acc.get('account_id') or acc.get('id'), platform, report)
                        cur = float(acc.get('balance', 0)) if acc.get('balance') not in (None, '') else 0
                        delta += cur - prev
                    platform_deltas[platform] = delta
                    platform_profits[platform] += delta
                print(f"✅ Прибыль по платформам рассчитана: {platform_deltas}")
            except Exception as e:
                print(f"❌ Ошибка при расчете прибыли по платформам: {str(e)}")
                import traceback
                traceback.print_exc()
                platform_deltas = {'bybit': 0, 'htx': 0, 'bliss': 0, 'gate': 0}
            
            print(f"🔧 Формируем детали отчета...")
            try:
                report_details.append({
                    'id': report.id,
                    'date': report.shift_date.isoformat(),
                    'shift_type': report.shift_type,
                    'total_requests': report.total_requests,
                    'bybit_requests': report.bybit_requests or 0,
                    'htx_requests': report.htx_requests or 0,
                    'bliss_requests': report.bliss_requests or 0,
                    'project_profit': round(profit_data['project_profit'], 2),
                    'salary_profit': round(profit_data['salary_profit'], 2),
                    'scam_amount': float(report.scam_amount or 0),
                    'scam_personal': report.scam_personal or False,
                    'dokidka_amount': float(report.dokidka_amount or 0),
                    'internal_transfer_amount': float(report.internal_transfer_amount or 0),
                    'platform_deltas': platform_deltas,
                    'balances': balances
                })
                print(f"✅ Детали отчета добавлены")
            except Exception as e:
                print(f"❌ Ошибка при формировании деталей отчета: {str(e)}")
                import traceback
                traceback.print_exc()
        
        print("🔧 Начинаем расчет статистики по ордерам...")
        print(f"🔧 Найдено ордеров: {len(orders)}")
        
        # Рассчитываем статистику на основе привязанных ордеров
        from utils import calculate_shift_stats_from_orders
        order_stats = calculate_shift_stats_from_orders(orders)
        
        # Дополнительная статистика по платформам
        platform_stats = {}
        for order in orders:
            platform = order.platform
            if platform not in platform_stats:
                platform_stats[platform] = 0
            platform_stats[platform] += 1
        
        # Статистика по статусам
        status_stats = {}
        for order in orders:
            status = order.status
            if status not in status_stats:
                status_stats[status] = 0
            status_stats[status] += 1
        
        # Объединяем статистику
        order_stats.update({
            'platform_stats': platform_stats,
            'status_stats': status_stats,
            'total_fees': sum(float(o.fees_usdt) for o in orders)
        })
        
        print("🔧 Начинаем расчет временной статистики...")
        # Временная статистика
        time_stats = {}
        try:
            if reports:
                first_report = min(reports, key=lambda r: r.shift_date)
                last_report = max(reports, key=lambda r: r.shift_date)
                
                time_stats = {
                    'first_report_date': first_report.shift_date.isoformat(),
                    'last_report_date': last_report.shift_date.isoformat(),
                    'total_period_days': (last_report.shift_date - first_report.shift_date).days + 1,
                    'active_days': len(set(r.shift_date for r in reports)),
                    'activity_ratio': len(set(r.shift_date for r in reports)) / ((last_report.shift_date - first_report.shift_date).days + 1)
                }
            print("✅ Временная статистика рассчитана")
        except Exception as e:
            print(f"❌ Ошибка при расчете временной статистики: {str(e)}")
            import traceback
            traceback.print_exc()
            time_stats = {}
        
        print("🔧 Начинаем расчет статистики по типам смен...")
        # Статистика по типам смен
        try:
            shift_stats = {
                'morning_shifts': len([r for r in reports if r.shift_type == 'morning']),
                'evening_shifts': len([r for r in reports if r.shift_type == 'evening']),
                'morning_profit': sum(calculate_report_profit(db.session, r)['salary_profit'] for r in reports if r.shift_type == 'morning'),
                'evening_profit': sum(calculate_report_profit(db.session, r)['salary_profit'] for r in reports if r.shift_type == 'evening')
            }
            print("✅ Статистика по типам смен рассчитана")
        except Exception as e:
            print(f"❌ Ошибка при расчете статистики по типам смен: {str(e)}")
            import traceback
            traceback.print_exc()
            shift_stats = {
                'morning_shifts': 0,
                'evening_shifts': 0,
                'morning_profit': 0,
                'evening_profit': 0
            }
        
        print("🔧 Начинаем расчет средних показателей...")
        # Средние показатели
        avg_stats = {}
        try:
            if reports:
                avg_stats = {
                    'avg_requests_per_shift': sum(r.total_requests or 0 for r in reports) / len(reports),
                    'avg_profit_per_shift': total_salary_profit / len(reports),
                    'avg_project_profit_per_shift': total_project_profit / len(reports),
                    'avg_bybit_per_shift': sum(r.bybit_requests or 0 for r in reports) / len(reports),
                    'avg_htx_per_shift': sum(r.htx_requests or 0 for r in reports) / len(reports),
                    'avg_bliss_per_shift': sum(r.bliss_requests or 0 for r in reports) / len(reports)
                }
            print("✅ Средние показатели рассчитаны")
        except Exception as e:
            print(f"❌ Ошибка при расчете средних показателей: {str(e)}")
            import traceback
            traceback.print_exc()
            avg_stats = {}
        
        print("🔧 Начинаем расчет лучших и худших показателей...")
        # Лучшие и худшие показатели
        best_worst = {}
        try:
            if reports:
                profits = [calculate_report_profit(db.session, r)['salary_profit'] for r in reports]
                best_report = max(reports, key=lambda r: calculate_report_profit(db.session, r)['salary_profit'])
                worst_report = min(reports, key=lambda r: calculate_report_profit(db.session, r)['salary_profit'])
                
                best_worst = {
                    'best_profit': {
                        'amount': max(profits),
                        'date': best_report.shift_date.isoformat(),
                        'shift_type': best_report.shift_type
                    },
                    'worst_profit': {
                        'amount': min(profits),
                        'date': worst_report.shift_date.isoformat(),
                        'shift_type': worst_report.shift_type
                    },
                    'most_requests': {
                        'count': max(r.total_requests or 0 for r in reports),
                        'date': max(reports, key=lambda r: r.total_requests or 0).shift_date.isoformat()
                    }
                }
            print("✅ Лучшие и худшие показатели рассчитаны")
        except Exception as e:
            print(f"❌ Ошибка при расчете лучших и худших показателей: {str(e)}")
            import traceback
            traceback.print_exc()
            best_worst = {}
        
        print("🔧 Формируем итоговый профиль...")
        # Формируем итоговый профиль
        try:
            profile = {
                'employee': {
                    'id': employee.id,
                    'name': employee.name,
                    'telegram': employee.telegram,
                    'salary_percent': employee.salary_percent or 30.0,
                    'is_active': employee.is_active,
                    'created_at': employee.created_at.isoformat() if employee.created_at else None
                },
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'basic_stats': basic_stats,
                'report_details': report_details,
                'order_stats': order_stats,
                'time_stats': time_stats,
                'shift_stats': shift_stats,
                'avg_stats': avg_stats,
                'best_worst': best_worst,
                'platform_profits': platform_profits
            }
            
            print("✅ Итоговый профиль сформирован")
            print("🔧 Отправляем ответ...")
            return jsonify(profile)
        except Exception as e:
            print(f"❌ Ошибка при формировании итогового профиля: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def process_shift_files(report_id, employee_id, shift_start_time, shift_end_time, files_data):
    """
    Обрабатывает файлы выгрузок для смены с автоматической проверкой времени
    
    Args:
        report_id: ID отчёта
        employee_id: ID сотрудника
        shift_start_time: время начала смены по МСК
        shift_end_time: время окончания смены по МСК
        files_data: словарь с файлами {platform: file_path}
    
    Returns:
        dict: статистика обработки файлов
    """
    from utils import link_orders_to_employee
    
    stats = {
        'total_orders': 0,
        'linked_orders': 0,
        'platforms_processed': [],
        'errors': []
    }
    
    try:
        # Получаем аккаунты сотрудника
        employee_accounts = Account.query.filter_by(
            employee_id=employee_id,
            is_active=True
        ).all()
        
        if not employee_accounts:
            stats['errors'].append('У сотрудника нет активных аккаунтов')
            return stats
        
        # Группируем аккаунты по платформам
        platform_accounts = {}
        for account in employee_accounts:
            if account.platform not in platform_accounts:
                platform_accounts[account.platform] = []
            platform_accounts[account.platform].append(account.id)
        
        # Обрабатываем каждый файл
        for platform, file_path in files_data.items():
            if not file_path or not os.path.exists(file_path):
                continue
                
            try:
                print(f"Обрабатываем файл {platform}: {file_path}")
                
                # Проверяем, есть ли у сотрудника аккаунты на этой платформе
                if platform not in platform_accounts:
                    print(f"У сотрудника нет аккаунтов на платформе {platform}")
                    continue
                
                # Обрабатываем файл для каждого аккаунта на этой платформе
                for account_id in platform_accounts[platform]:
                    account_stats = process_platform_file(
                        file_path,
                        platform,
                        [account_id],  # Передаем только один аккаунт
                        shift_start_time,
                        shift_end_time,
                        report_id,
                        employee_id
                    )
                    
                    stats['total_orders'] += account_stats.get('total_orders', 0)
                    stats['linked_orders'] += account_stats.get('linked_orders', 0)
                
                if platform not in stats['platforms_processed']:
                    stats['platforms_processed'].append(platform)
                
                print(f"Обработано {stats['total_orders']} ордеров для {platform}, создано {stats['linked_orders']} новых")
                
            except Exception as e:
                error_msg = f"Ошибка обработки файла {platform}: {str(e)}"
                stats['errors'].append(error_msg)
                print(error_msg)
                continue
        
        return stats
        
    except Exception as e:
        stats['errors'].append(f"Общая ошибка обработки файлов: {str(e)}")
        return stats

@app.route('/api/employee-accounts/<int:employee_id>', methods=['GET'])
def get_employee_accounts(employee_id):
    """Возвращает все активные аккаунты, сгруппированные по площадкам"""
    try:
        # Получаем все активные аккаунты (не привязанные к конкретному сотруднику)
        accounts = Account.query.filter_by(is_active=True).all()
        
        # Группируем по площадкам
        accounts_by_platform = {}
        for account in accounts:
            platform = account.platform
            if platform not in accounts_by_platform:
                accounts_by_platform[platform] = []
            
            accounts_by_platform[platform].append({
                'id': account.id,
                'account_name': account.account_name,
                'platform': account.platform
            })
        
        return jsonify({
            'success': True,
            'accounts': accounts_by_platform
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def validate_shift_time_and_files(shift_start_time, shift_end_time, files_data, employee_accounts):
    """
    Валидирует время смены и проверяет соответствие файлов выгрузок аккаунтам сотрудника
    
    Args:
        shift_start_time: время начала смены по МСК
        shift_end_time: время окончания смены по МСК
        files_data: словарь с файлами {platform: file_path}
        employee_accounts: список аккаунтов сотрудника
    
    Returns:
        dict: результат валидации
    """
    validation_result = {
        'is_valid': True,
        'errors': [],
        'warnings': [],
        'file_validation': {}
    }
    
    # Проверяем время смены
    if not shift_start_time or not shift_end_time:
        validation_result['is_valid'] = False
        validation_result['errors'].append('Необходимо указать время начала и окончания смены')
        return validation_result
    
    if shift_start_time >= shift_end_time:
        validation_result['is_valid'] = False
        validation_result['errors'].append('Время начала смены должно быть раньше времени окончания')
        return validation_result
    
    # Проверяем длительность смены (не более 24 часов)
    shift_duration = shift_end_time - shift_start_time
    if shift_duration.total_seconds() > 24 * 3600:
        validation_result['warnings'].append('Длительность смены превышает 24 часа')
    
    # Получаем аккаунты сотрудника по площадкам
    employee_platforms = set(acc.platform for acc in employee_accounts)
    
    # Проверяем соответствие файлов выгрузок аккаунтам сотрудника
    for platform, file_path in files_data.items():
        if not file_path or not os.path.exists(file_path):
            continue
            
        if platform not in employee_platforms:
            validation_result['warnings'].append(
                f'Файл выгрузки {platform} загружен, но у сотрудника нет аккаунтов на этой площадке'
            )
        
        # Проверяем содержимое файла
        try:
            orders_data = parse_orders_file(
                file_path, 
                platform, 
                shift_start_time, 
                shift_end_time,
                os.path.basename(file_path)
            )
            
            # Проверяем, есть ли ордера в файле для аккаунтов сотрудника
            employee_account_names = [acc.account_name for acc in employee_accounts if acc.platform == platform]
            relevant_orders = [
                order for order in orders_data 
                if order.get('account_name') in employee_account_names
            ]
            
            validation_result['file_validation'][platform] = {
                'total_orders': len(orders_data),
                'employee_orders': len(relevant_orders),
                'account_names': employee_account_names,
                'has_orders_in_shift': len(relevant_orders) > 0
            }
            
            if len(relevant_orders) == 0:
                validation_result['warnings'].append(
                    f'В файле {platform} не найдено ордеров для аккаунтов сотрудника в указанное время смены'
                )
                
        except Exception as e:
            validation_result['errors'].append(f'Ошибка обработки файла {platform}: {str(e)}')
    
    return validation_result

@app.route('/api/validate-shift', methods=['POST'])
def validate_shift():
    """Валидирует время смены и файлы выгрузок"""
    try:
        if request.content_type and request.content_type.startswith('multipart/form-data'):
            form = request.form
            files = request.files
            
            # Получаем данные формы
            employee_id = form.get('employee_id')
            shift_start_time_str = form.get('shift_start_time')
            shift_end_time_str = form.get('shift_end_time')
            
            if not employee_id or not shift_start_time_str or not shift_end_time_str:
                return jsonify({'error': 'Необходимо указать сотрудника и время смены'}), 400
            
            # Парсим время
            try:
                shift_start_time = datetime.strptime(shift_start_time_str, '%Y-%m-%dT%H:%M')
                shift_end_time = datetime.strptime(shift_end_time_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                return jsonify({'error': 'Неверный формат времени'}), 400
            
            # Получаем аккаунты сотрудника
            employee_accounts = Account.query.filter_by(
                employee_id=employee_id,
                is_active=True
            ).all()
            
            if not employee_accounts:
                return jsonify({'error': 'У сотрудника нет активных аккаунтов'}), 400
            
            # Собираем файлы
            files_data = {}
            file_keys = ['bybit_file', 'htx_file', 'bliss_file']
            
            for key in file_keys:
                if key in files and files[key].filename:
                    file = files[key]
                    if file and allowed_file(file.filename):
                        if not validate_file_size(file):
                            return jsonify({'error': f'Файл {file.filename} слишком большой (максимум 16MB)'}), 400
                        
                        # Сохраняем временный файл для валидации
                        filename = secure_filename(file.filename)
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        filename = f"temp_{timestamp}_{filename}"
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(file_path)
                        
                        platform = key.replace('_file', '')
                        files_data[platform] = file_path
            
            # Валидируем
            validation_result = validate_shift_time_and_files(
                shift_start_time, 
                shift_end_time, 
                files_data, 
                employee_accounts
            )
            
            # Удаляем временные файлы
            for file_path in files_data.values():
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            return jsonify(validation_result)
            
        else:
            return jsonify({'error': 'Неподдерживаемый тип контента'}), 400
            
    except Exception as e:
        return jsonify({'error': f'Ошибка валидации: {str(e)}'}), 500

@app.route('/api/reports/create-shift', methods=['POST'])
def create_shift_report():
    """Создает отчёт по смене с автоматической обработкой файлов выгрузок"""
    try:
        # Получаем данные из формы
        employee_id = request.form.get('employee_id')
        shift_date = request.form.get('shift_date')
        shift_start_time = request.form.get('shift_start_time')
        shift_end_time = request.form.get('shift_end_time')
        selected_accounts_json = request.form.get('selected_accounts', '{}')
        balances_json = request.form.get('balances', '{}')
        
        # Валидация обязательных полей
        if not all([employee_id, shift_date, shift_start_time, shift_end_time]):
            return jsonify({'error': 'Заполните все обязательные поля'}), 400
        
        # Парсим выбранные аккаунты и балансы
        try:
            selected_accounts = json.loads(selected_accounts_json)
            balances = json.loads(balances_json)
        except json.JSONDecodeError:
            return jsonify({'error': 'Неверный формат данных аккаунтов или балансов'}), 400
        
        # Преобразуем время в datetime объекты
        try:
            shift_start_dt = datetime.strptime(shift_start_time, '%Y-%m-%dT%H:%M')
            shift_end_dt = datetime.strptime(shift_end_time, '%Y-%m-%dT%H:%M')
            print(f"DEBUG SHIFT: Время смены (МСК): {shift_start_dt} - {shift_end_dt}")
        except ValueError:
            return jsonify({'error': 'Неверный формат времени'}), 400
        
        # Проверяем, что время начала меньше времени окончания
        if shift_start_dt >= shift_end_dt:
            return jsonify({'error': 'Время начала смены должно быть меньше времени окончания'}), 400
        
        # Определяем тип смены на основе времени начала
        shift_type = 'morning' if shift_start_dt.hour < 16 else 'evening'
        
        # Создаем отчет
        report = ShiftReport(
            employee_id=int(employee_id),
            shift_date=datetime.strptime(shift_date, '%Y-%m-%d').date(),
            shift_type=shift_type,
            shift_start_time=shift_start_dt,
            shift_end_time=shift_end_dt,
            balances_json=balances_json,  # Сохраняем балансы
            scam_amount=safe_float(request.form.get('scam_amount', 0)),
            scam_comment=request.form.get('scam_comment', ''),
            scam_personal=parse_bool(request.form.get('scam_personal', False)),
            dokidka_amount=safe_float(request.form.get('dokidka_amount', 0)),
            dokidka_comment=request.form.get('dokidka_comment', ''),
            internal_transfer_amount=safe_float(request.form.get('internal_transfer_amount', 0)),
            internal_transfer_comment=request.form.get('internal_transfer_comment', ''),
            appeal_amount=safe_float(request.form.get('appeal_amount', 0)),
            appeal_comment=request.form.get('appeal_comment', ''),
            appeal_deducted=parse_bool(request.form.get('appeal_deducted', False))  # Добавляем новое поле
        )
        
        # Сохраняем фотографии
        # Проверяем существование директории uploads
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
            
        if 'start_photo' in request.files:
            file = request.files['start_photo']
            if file.filename:
                if not allowed_file(file.filename):
                    return jsonify({'error': f'Недопустимый тип файла для фото начала смены: {file.filename}. Разрешены только: png, jpg, jpeg, webp'}), 400
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                report.start_photo = filename
                
        if 'end_photo' in request.files:
            file = request.files['end_photo']
            if file.filename:
                if not allowed_file(file.filename):
                    return jsonify({'error': f'Недопустимый тип файла для фото конца смены: {file.filename}. Разрешены только: png, jpg, jpeg, webp'}), 400
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                report.end_photo = filename
        
        # Сохраняем отчет в базу
        db.session.add(report)
        db.session.commit()
        
        # Если скам отмечен как личный, сохраняем его в историю
        if report.scam_amount and report.scam_personal:
            scam_history = EmployeeScamHistory(
                employee_id=int(employee_id),
                shift_report_id=report.id,
                amount=report.scam_amount,
                date=report.shift_date,
                comment=report.scam_comment
            )
            db.session.add(scam_history)
            db.session.commit()
        
        # Обрабатываем файлы выгрузок и привязываем ордера
        stats = {
            'total_orders': 0,
            'linked_orders': 0,
            'platforms_processed': [],
            'errors': []
        }
        
        # Обрабатываем файлы для каждого аккаунта
        for platform in ['bybit', 'htx', 'bliss', 'gate']:
            if platform in selected_accounts and selected_accounts[platform]:
                platform_stats = {
                    'total_orders': 0,
                    'linked_orders': 0,
                    'errors': []
                }
                
                for account_id in selected_accounts[platform]:
                    file_key = f'file_{platform}_{account_id}'
                    if file_key in request.files:
                        file = request.files[file_key]
                        if file.filename:
                            try:
                                # Сохраняем файл и получаем путь
                                file_path = save_report_file(file, platform, report.id)
                                if not file_path:
                                    continue
                                
                                print(f"Обрабатываем файл {platform} для аккаунта {account_id}: {file_path}")
                                
                                # Обрабатываем файл и привязываем ордера для конкретного аккаунта
                                account_stats = process_platform_file(
                                    file_path, 
                                    platform, 
                                    [account_id],  # Передаем только один аккаунт
                                    shift_start_dt, 
                                    shift_end_dt,
                                    report.id,
                                    int(employee_id)
                                )
                                
                                platform_stats['total_orders'] += account_stats.get('total_orders', 0)
                                platform_stats['linked_orders'] += account_stats.get('linked_orders', 0)
                                
                                if account_stats.get('errors'):
                                    platform_stats['errors'].extend(account_stats['errors'])
                                
                            except Exception as e:
                                error_msg = f'Ошибка обработки файла {platform} для аккаунта {account_id}: {str(e)}'
                                platform_stats['errors'].append(error_msg)
                                print(error_msg)
                
                # Обновляем общую статистику
                stats['total_orders'] += platform_stats['total_orders']
                stats['linked_orders'] += platform_stats['linked_orders']
                
                if platform_stats['total_orders'] > 0:
                    stats['platforms_processed'].append(platform.upper())
                
                if platform_stats['errors']:
                    stats['errors'].extend(platform_stats['errors'])
        
        return jsonify({
            'id': report.id,
            'message': 'Report created successfully',
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({'error': f'Ошибка создания отчёта: {str(e)}'}), 500


def process_platform_file(file_path, platform, account_ids, shift_start_dt, shift_end_dt, report_id, employee_id):
    """Обрабатывает файл выгрузки для конкретной площадки"""
    print(f"\nDEBUG SHIFT: Обработка файла {platform}")
    print(f"DEBUG SHIFT: Время смены {shift_start_dt} - {shift_end_dt}")
    
    stats = {
        'total_orders': 0,
        'linked_orders': 0,
        'errors': []
    }
    
    try:
        # Получаем аккаунты для проверки
        accounts = Account.query.filter(Account.id.in_(account_ids)).all()
        account_names = [acc.account_name for acc in accounts]
        
        if not account_names:
            stats['errors'].append(f'Не найдены аккаунты с ID: {account_ids}')
            return stats
        
        # Читаем файл в зависимости от платформы
        orders = parse_orders_file(file_path, platform)
        if not orders:
            stats['errors'].append(f'Не удалось прочитать файл для платформы: {platform}')
            return stats
        
        stats['total_orders'] = len(orders)
        
        # Если в выгрузке отсутствует поле account_name, привяжем все ордера к текущему аккаунту
        # (передаём всегда только один account_id на вызов)
        if len(account_names) == 1:
            default_account_name = account_names[0]
        else:
            default_account_name = None
        
        # Приводим имена аккаунтов к нижнему регистру для сравнения
        account_names_lower = [name.lower() for name in account_names]
        
        # Фильтруем ордера по аккаунту и времени
        account_orders = []
        
        for order in orders:
            # Время уже сконвертировано в parse_orders_file
            order_time = order['executed_at']
            print(f"\nDEBUG FILTER: ========== Проверка ордера {order['order_id']} ==========")
            print(f"DEBUG FILTER: Время ордера (МСК): {order_time}")
            print(f"DEBUG FILTER: Диапазон смены (МСК): {shift_start_dt} - {shift_end_dt}")
            print(f"DEBUG FILTER: Время больше начала смены: {order_time >= shift_start_dt}")
            print(f"DEBUG FILTER: Время меньше конца смены: {order_time <= shift_end_dt}")
            
            # Проверяем попадание в диапазон смены
            if shift_start_dt <= order_time <= shift_end_dt:  # попадает во временной диапазон
                print(f"DEBUG FILTER: >>> Ордер {order['order_id']} ПОПАДАЕТ в смену <<<")
                account_orders.append(order)
            else:
                print(f"DEBUG FILTER: >>> Ордер {order['order_id']} НЕ попадает в смену <<<")
            print(f"DEBUG FILTER: ================================================\n")
        
        # Сохраняем отфильтрованные ордера
        created_count = 0
        for order in account_orders:
            try:
                # Проверяем, что ордер еще не существует
                existing_order = Order.query.filter_by(
                    order_id=order['order_id'],
                    platform=platform
                ).first()
                
                if existing_order:
                    print(f"Ордер уже существует: {order['order_id']}")
                    continue
                
                # Создаем новый ордер
                new_order = Order(
                    order_id=order['order_id'],
                    employee_id=employee_id,
                    platform=platform,
                    account_name=default_account_name,  # Всегда используем имя выбранного аккаунта
                    symbol=order['symbol'],
                    side=order['side'],
                    quantity=order['quantity'],
                    price=order['price'],
                    total_usdt=order['total_usdt'],
                    fees_usdt=order.get('fees_usdt', 0),
                    status=order.get('status', 'filled'),
                    executed_at=order['executed_at']
                )
                
                db.session.add(new_order)
                created_count += 1
                print(f"Создан новый ордер: {order['order_id']} для аккаунта {order.get('account_name')}")
                
            except Exception as e:
                print(f"Ошибка сохранения ордера {order.get('order_id')}: {str(e)}")
                continue
        
        # Сохраняем изменения
        db.session.commit()
        
        stats['linked_orders'] = created_count
        print(f"Обработано {len(account_orders)} ордеров для {platform}, создано {created_count} новых")
        
        return stats
        
    except Exception as e:
        stats['errors'].append(str(e))
        return stats

@app.route('/api/employee-scams/<int:employee_id>', methods=['GET'])
def get_employee_scams(employee_id):
    """Получает историю скамов сотрудника"""
    try:
        # Проверяем существование сотрудника
        employee = Employee.query.get(employee_id)
        if not employee:
            return jsonify({'error': 'Сотрудник не найден'}), 404
            
        # Получаем все скамы сотрудника, сортируем по дате (сначала новые)
        scams = EmployeeScamHistory.query.filter_by(employee_id=employee_id).order_by(EmployeeScamHistory.date.desc()).all()
        
        # Форматируем данные для ответа
        scams_data = []
        total_amount = 0
        
        for scam in scams:
            scam_data = {
                'id': scam.id,
                'date': scam.date.strftime('%Y-%m-%d'),
                'amount': float(scam.amount),
                'comment': scam.comment,
                'shift_report_id': scam.shift_report_id
            }
            scams_data.append(scam_data)
            total_amount += float(scam.amount)
        
        return jsonify({
            'employee_id': employee_id,
            'employee_name': employee.name,
            'scams': scams_data,
            'total_amount': total_amount
        })
        
    except Exception as e:
        return jsonify({'error': f'Ошибка получения истории скамов: {str(e)}'}), 500

@app.route('/api/settings/salary', methods=['GET'])
def get_salary_settings():
    """Получает настройки расчета зарплаты"""
    try:
        settings = SalarySettings.query.first()
        if not settings:
            settings = SalarySettings()
            db.session.add(settings)
            db.session.commit()
            
        return jsonify({
            'base_percent': settings.base_percent,
            'min_requests_per_day': settings.min_requests_per_day,
            'bonus_percent': settings.bonus_percent,
            'bonus_requests_threshold': settings.bonus_requests_threshold
        })
    except Exception as e:
        print('Error getting salary settings:', e)
        return jsonify({'error': 'Ошибка при получении настроек'}), 500

@app.route('/api/settings/salary', methods=['POST'])
def update_salary_settings():
    """Обновляет настройки расчета зарплаты"""
    try:
        data = request.get_json()
        
        # Проверяем пароль администратора
        if not check_admin_password(data.get('password')):
            return jsonify({'error': 'Неверный пароль администратора'}), 403
            
        settings = SalarySettings.query.first()
        if not settings:
            settings = SalarySettings()
            db.session.add(settings)
            
        # Обновляем настройки
        settings.base_percent = data.get('base_percent', settings.base_percent)
        settings.min_requests_per_day = data.get('min_requests_per_day', settings.min_requests_per_day)
        settings.bonus_percent = data.get('bonus_percent', settings.bonus_percent)
        settings.bonus_requests_threshold = data.get('bonus_requests_threshold', settings.bonus_requests_threshold)
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        print('Error updating salary settings:', e)
        return jsonify({'error': 'Ошибка при обновлении настроек'}), 500




if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Добавляем индексы для оптимизации производительности
        try:
            # Используем новый синтаксис SQLAlchemy для выполнения SQL
            from sqlalchemy import text
            
            # Индексы для частых запросов
            db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_shift_report_date ON shift_report(shift_date)'))
            db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_shift_report_employee ON shift_report(employee_id)'))
            db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_shift_report_date_employee ON shift_report(shift_date, employee_id)'))
            db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_account_platform ON account(platform)'))
            db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_account_employee ON account(employee_id)'))
            db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_balance_history_date ON account_balance_history(shift_date)'))
            db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_balance_history_account ON account_balance_history(account_id)'))
            
            # Коммитим изменения
            db.session.commit()
            app.logger.info('Индексы базы данных созданы успешно')
        except Exception as e:
            app.logger.warning(f'Ошибка при создании индексов: {str(e)}')
    
    # Настройки для продакшена
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', 5000))
    
    app.run(debug=debug_mode, host=host, port=port) 