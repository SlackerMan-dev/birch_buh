@echo off
echo 🚀 Запуск Flask приложения для локальной сети
echo ================================================

echo 📊 Проверка настроек...
if not exist app.py (
    echo ❌ Файл app.py не найден!
    pause
    exit /b 1
)

echo 🔧 Установка переменных окружения...
set FLASK_HOST=0.0.0.0
set FLASK_PORT=5000
set FLASK_ENV=production

echo 🚀 Запуск приложения...
echo.
echo 📱 Приложение будет доступно по адресу:
echo 🌐 http://YOUR_LOCAL_IP:5000
echo.
echo 💡 Чтобы узнать ваш IP адрес, выполните: ipconfig
echo.

python app.py

pause 