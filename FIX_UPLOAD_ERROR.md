# Исправление ошибки 404 при загрузке файлов

## Проблема
При попытке загрузить файл с ордерами появляется ошибка:
```
Failed to load resource: the server responded with a status of 404 (NOT FOUND)
POST http://localhost:5000/api/orders/upload 404 (NOT FOUND)
```

## Причина
Сервер не может найти API endpoint `/api/orders/upload` из-за отсутствия зависимостей `pandas` и `openpyxl`.

## Решение

### Шаг 1: Остановить сервер
Если сервер запущен, остановите его нажатием `Ctrl+C` в терминале.

### Шаг 2: Установить зависимости
Выполните одну из команд:

**Вариант 1 - Автоматическая установка:**
```bash
python install_deps.py
```

**Вариант 2 - Ручная установка:**
```bash
pip install pandas openpyxl xlrd
```

**Вариант 3 - Через bat файл (Windows):**
Дважды кликните на файл `install_deps.bat`

### Шаг 3: Проверить установку
```bash
python -c "import pandas; print('✅ pandas установлен:', pandas.__version__)"
python -c "import openpyxl; print('✅ openpyxl установлен:', openpyxl.__version__)"
```

### Шаг 4: Запустить сервер
```bash
python app.py
```

### Шаг 5: Проверить работу
1. Откройте браузер: http://localhost:5000
2. Перейдите в раздел "История ордеров"
3. Нажмите кнопку "Загрузить выгрузку"
4. Попробуйте загрузить файл

## Альтернативное решение (если проблемы с установкой)

Если у вас возникают проблемы с установкой pandas, можно использовать упрощенную версию без pandas:

1. Откройте файл `app.py`
2. Найдите строку с `import pandas as pd`
3. Замените блок импорта на:
```python
# Временно отключаем pandas
PANDAS_AVAILABLE = False
pd = None
```

4. Перезапустите сервер

**Примечание:** Без pandas функция загрузки файлов работать не будет, но остальные функции системы будут работать нормально.

## Проверка работы API

Для проверки работы API можно выполнить:
```bash
python test_upload.py
```

Этот скрипт создаст тестовые файлы и проверит работу загрузки.

## Контакты
Если проблема не решается, обратитесь к разработчику с описанием ошибки. 