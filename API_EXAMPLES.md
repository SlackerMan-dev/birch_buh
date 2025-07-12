# 🔌 API Примеры использования

## Обзор API

Система предоставляет REST API для интеграции с внешними системами и автоматизации процессов.

## 🔑 Базовый URL
```
http://localhost:5000/api/
```

## 📊 Примеры запросов

### 1. Получение списка сотрудников

```bash
curl -X GET http://localhost:5000/api/employees
```

**Ответ:**
```json
[
  {
    "id": 1,
    "name": "Алексей Петров",
    "bybit_account": "alex_petrov_bybit",
    "shift": "morning",
    "created_at": "2024-01-15T10:30:00"
  }
]
```

### 2. Добавление нового сотрудника

```bash
curl -X POST http://localhost:5000/api/employees \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Иван Иванов",
    "bybit_account": "ivan_ivanov_bybit",
    "shift": "evening"
  }'
```

### 3. Получение данных дашборда

```bash
curl -X GET http://localhost:5000/api/dashboard
```

**Ответ:**
```json
{
  "total_profit": 15420.50,
  "total_volume": 125000.00,
  "total_orders": 450,
  "total_successful": 405,
  "success_rate": 90.0,
  "morning_profit": 8200.25,
  "evening_profit": 7220.25,
  "employee_stats": [
    {
      "id": 1,
      "name": "Алексей Петров",
      "shift": "morning",
      "total_profit": 3200.50,
      "total_orders": 95,
      "success_rate": 92.6
    }
  ]
}
```

### 4. Получение отчетов с фильтрацией

```bash
curl -X GET "http://localhost:5000/api/reports?start_date=2024-01-01&end_date=2024-01-31&employee_id=1"
```

### 5. Создание отчета о смене

```bash
curl -X POST http://localhost:5000/api/reports \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": 1,
    "platform_id": 1,
    "shift_date": "2024-01-15",
    "shift_type": "morning",
    "total_orders": 15,
    "successful_orders": 14,
    "failed_orders": 1,
    "total_volume_usdt": 2500.00,
    "total_profit_usdt": 75.50,
    "total_fees_usdt": 5.25,
    "total_working_hours": 8.5
  }'
```

## 🔄 Интеграция с Python

### Пример скрипта для автоматического импорта данных

```python
import requests
import json
from datetime import datetime

class ArbitrageReporter:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
    
    def get_employees(self):
        """Получение списка сотрудников"""
        response = requests.get(f"{self.base_url}/api/employees")
        return response.json()
    
    def create_report(self, report_data):
        """Создание отчета о смене"""
        response = requests.post(
            f"{self.base_url}/api/reports",
            headers={"Content-Type": "application/json"},
            data=json.dumps(report_data)
        )
        return response.json()
    
    def get_dashboard_data(self):
        """Получение данных дашборда"""
        response = requests.get(f"{self.base_url}/api/dashboard")
        return response.json()

# Пример использования
reporter = ArbitrageReporter()

# Получаем данные дашборда
dashboard = reporter.get_dashboard_data()
print(f"Общая прибыль: ${dashboard['total_profit']:.2f}")

# Создаем отчет
new_report = {
    "employee_id": 1,
    "platform_id": 1,
    "shift_date": datetime.now().strftime("%Y-%m-%d"),
    "shift_type": "morning",
    "total_orders": 20,
    "successful_orders": 18,
    "failed_orders": 2,
    "total_volume_usdt": 3000.00,
    "total_profit_usdt": 90.00,
    "total_fees_usdt": 6.00,
    "total_working_hours": 8.0
}

result = reporter.create_report(new_report)
print(f"Отчет создан: {result}")
```

## 🔗 Интеграция с Telegram ботом

### Пример уведомлений о результатах

```python
import requests
import telegram
from datetime import datetime, timedelta

class ArbitrageTelegramBot:
    def __init__(self, bot_token, chat_id, api_url="http://localhost:5000"):
        self.bot = telegram.Bot(token=bot_token)
        self.chat_id = chat_id
        self.api_url = api_url
    
    def send_daily_report(self):
        """Отправка ежедневного отчета"""
        # Получаем данные за сегодня
        today = datetime.now().strftime("%Y-%m-%d")
        response = requests.get(f"{self.api_url}/api/reports?start_date={today}&end_date={today}")
        reports = response.json()
        
        if reports:
            total_profit = sum(r['total_profit_usdt'] for r in reports)
            total_volume = sum(r['total_volume_usdt'] for r in reports)
            
            message = f"""
📊 Ежедневный отчет арбитража
            
💰 Общая прибыль: ${total_profit:.2f}
📈 Общий объем: ${total_volume:.2f}
📋 Количество смен: {len(reports)}
            
Дата: {today}
            """
            
            self.bot.send_message(chat_id=self.chat_id, text=message)
    
    def send_alert(self, message):
        """Отправка уведомления"""
        self.bot.send_message(chat_id=self.chat_id, text=f"🚨 {message}")

# Пример использования
# bot = ArbitrageTelegramBot("YOUR_BOT_TOKEN", "YOUR_CHAT_ID")
# bot.send_daily_report()
```

## 📊 Интеграция с Excel

### Экспорт данных в Excel

```python
import pandas as pd
import requests
from datetime import datetime, timedelta

def export_reports_to_excel(start_date, end_date, filename="arbitrage_reports.xlsx"):
    """Экспорт отчетов в Excel"""
    
    # Получаем отчеты
    response = requests.get(f"http://localhost:5000/api/reports?start_date={start_date}&end_date={end_date}")
    reports = response.json()
    
    # Получаем сотрудников для сопоставления
    employees_response = requests.get("http://localhost:5000/api/employees")
    employees = {emp['id']: emp['name'] for emp in employees_response.json()}
    
    # Создаем DataFrame
    df = pd.DataFrame(reports)
    df['employee_name'] = df['employee_id'].map(employees)
    df['shift_date'] = pd.to_datetime(df['shift_date'])
    
    # Сохраняем в Excel
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Reports', index=False)
        
        # Создаем сводную таблицу
        pivot = df.pivot_table(
            values=['total_profit_usdt', 'total_volume_usdt', 'total_orders'],
            index='employee_name',
            aggfunc='sum'
        )
        pivot.to_excel(writer, sheet_name='Summary')
    
    print(f"Данные экспортированы в {filename}")

# Пример использования
# export_reports_to_excel("2024-01-01", "2024-01-31")
```

## 🔐 Безопасность

### Рекомендации по безопасности

1. **Ограничение доступа**: Настройте firewall для ограничения доступа к API
2. **Аутентификация**: Добавьте API ключи или токены для защиты
3. **Валидация данных**: Проверяйте все входящие данные
4. **Логирование**: Ведите логи всех API запросов

### Пример с аутентификацией

```python
import requests
from functools import wraps

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != 'your-secret-key':
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Применение к API endpoints
@app.route('/api/employees', methods=['GET'])
@require_api_key
def get_employees():
    # ... код функции
```

## 📈 Мониторинг и аналитика

### Пример скрипта для мониторинга эффективности

```python
import requests
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

def analyze_performance(days=30):
    """Анализ эффективности за период"""
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    response = requests.get(f"http://localhost:5000/api/reports?start_date={start_date}&end_date={end_date}")
    reports = response.json()
    
    # Анализ по дням
    daily_profit = {}
    for report in reports:
        date = report['shift_date']
        if date not in daily_profit:
            daily_profit[date] = 0
        daily_profit[date] += report['total_profit_usdt']
    
    # Создаем график
    dates = sorted(daily_profit.keys())
    profits = [daily_profit[date] for date in dates]
    
    plt.figure(figsize=(12, 6))
    plt.plot(dates, profits, marker='o')
    plt.title('Прибыль по дням')
    plt.xlabel('Дата')
    plt.ylabel('Прибыль (USDT)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('profit_trend.png')
    plt.show()
    
    return daily_profit

# Пример использования
# performance = analyze_performance(30)
```

---

**Эти примеры помогут вам интегрировать систему отчетности с вашими существующими процессами и автоматизировать сбор данных.** 