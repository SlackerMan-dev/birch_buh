# 🌐 Настройка Cloudflare Tunnel - Пошаговая инструкция

## 🎯 Что мы делаем
Создаем туннель от вашего компьютера в интернет, чтобы коллеги могли получить доступ к приложению.

## 📋 Шаг 1: Запуск Flask приложения

1. **Откройте командную строку** в папке с проектом
2. **Запустите Flask:**
   ```bash
   python app.py
   ```
3. **Дождитесь сообщения:** "Running on http://127.0.0.1:5000"
4. **Оставьте это окно открытым**

## 📋 Шаг 2: Запуск Cloudflare туннеля

1. **Откройте новое окно командной строки** в той же папке
2. **Запустите туннель:**
   ```bash
   cloudflared.exe tunnel --url http://localhost:5000
   ```
3. **Дождитесь появления URL** вида:
   ```
   https://random-words-1234.trycloudflare.com
   ```

## 🎉 Результат

- **Локальный доступ:** http://localhost:5000
- **Интернет доступ:** https://random-words-1234.trycloudflare.com

## 📱 Поделитесь ссылкой

Отправьте интернет-ссылку коллегам. Они смогут войти, используя пароль приложения.

## ⚠️ Важно

- **Не закрывайте оба окна** командной строки
- **URL меняется** при перезапуске туннеля
- **Туннель бесплатный** и работает стабильно

## 🛠️ Если что-то не работает

### Проблема: "python не найден"
**Решение:** Установите Python с https://python.org

### Проблема: "cloudflared не найден"
**Решение:** Скачайте cloudflared.exe с https://github.com/cloudflare/cloudflared/releases/latest

### Проблема: "Порт 5000 занят"
**Решение:** Закройте другие приложения или измените порт в app.py

## 🚀 Быстрый запуск

Если у вас есть файл `start_cloudflare_tunnel.bat`:
1. Запустите Flask: `python app.py`
2. Запустите туннель: двойной щелчок по `start_cloudflare_tunnel.bat` 