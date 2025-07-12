# Правильный маппинг полей из Excel файла

## Структура файла Excel (как в вашем примере)

| Order No. | Cryptocurrency | Type | Fiat Amount | Currency | Price | Currency | Coin Amount | Cryptocurrency | Status | Time |
|-----------|----------------|------|-------------|----------|-------|----------|-------------|----------------|---------|------|
| 1912886... | USDT | SELL | 1479.75 | RUB | 83.75 | RUB | 157.0000 | USDT | Completed | 2025-04-17 |

## Правильный маппинг полей

### ✅ Исправленный маппинг:

| Колонка в системе | ← Берется из Excel | Пример значения |
|-------------------|-------------------|-----------------|
| **ID ордера** | `Order No.` | 1912886982052605952 |
| **Сотрудник** | Выбирается при загрузке | Иван |
| **Платформа** | Выбирается при загрузке | Bybit |
| **Аккаунт** | Выбирается при загрузке | Account1 |
| **Пара** | `Cryptocurrency` | USDT |
| **Сторона** | `Type` | SELL → Продажа |
| **Цена** | `Price` | 83.75 |
| **Объем (RUB)** | `Fiat Amount` | 1479.75 |
| **Объем (USDT)** | `Coin Amount` | 157.0000 |
| **Статус** | `Status` | Completed → Завершен |
| **Дата выполнения** | `Time` | 2025-04-17 15:12:51 |

### ❌ Убранные колонки:
- **Количество** - удалена полностью

## Изменения в коде

### 1. Парсер файлов (`app.py`)
```python
# Ищем нужные поля в Excel
elif any(x in col_lower for x in ['cryptocurrency', 'symbol', 'pair']):
    symbol = col_value.upper()  # Пара

elif any(x in col_lower for x in ['fiat amount', 'fiatamount']):
    fiat_amount = float(col_value)  # Объем (RUB)

elif any(x in col_lower for x in ['coin amount', 'coinamount']):
    coin_amount = float(col_value)  # Объем (USDT)

elif any(x in col_lower for x in ['price']):
    price = float(col_value)  # Цена

elif any(x in col_lower for x in ['status']):
    status = col_value  # Статус (Completed → filled)
```

### 2. Возвращаемые данные
```python
return {
    'order_id': order_id,
    'symbol': symbol,           # Пара
    'side': side,              # Сторона
    'quantity': coin_amount,    # Объем (USDT) - из Coin Amount
    'price': price,            # Цена - из Price  
    'total_usdt': fiat_amount, # Объем (RUB) - из Fiat Amount
    'fees_usdt': 0,
    'status': status,          # Статус - из Status
    'executed_at': executed_at
}
```

### 3. Таблица в интерфейсе
```javascript
// Заголовки
<th>Цена</th>           // order.price
<th>Объем (RUB)</th>    // order.total_usdt (из Fiat Amount)
<th>Объем (USDT)</th>   // order.quantity (из Coin Amount)
<th>Статус</th>         // order.status (из Status)

// Данные
<td>{parseFloat(order.price).toFixed(2)}</td>
<td>{parseFloat(order.total_usdt).toFixed(2)}</td>
<td>{parseFloat(order.quantity).toFixed(2)}</td>
<td>{getStatusText(order.status)}</td>
```

## Результат

Теперь система правильно читает файлы Excel и отображает:
- **Цена**: 83.75 (из Price)
- **Объем (RUB)**: 1479.75 (из Fiat Amount)
- **Объем (USDT)**: 157.00 (из Coin Amount)
- **Статус**: Завершен (из Status: Completed)

Статистика сверху:
- **Общий объем (RUB)**: сумма всех Fiat Amount
- **Общий объем (USDT)**: сумма всех Coin Amount

## Поддерживаемые названия столбцов

Система распознает различные варианты названий:
- **Order No**: `order no`, `order id`, `orderid`, `order_id`, `номер`
- **Cryptocurrency**: `cryptocurrency`, `symbol`, `pair`, `пара`, `инструмент`
- **Type**: `side`, `type`, `тип`, `направление`
- **Fiat Amount**: `fiat amount`, `fiatamount`, `fiat_amount`
- **Coin Amount**: `coin amount`, `coinamount`, `coin_amount`
- **Price**: `price`, `цена`, `курс`
- **Status**: `status`, `статус`
- **Time**: `time`, `date`, `время`, `дата`, `created` 