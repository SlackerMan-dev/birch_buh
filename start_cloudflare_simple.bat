@echo off
echo 🌐 Запуск Flask + Cloudflare Tunnel
echo ===================================

echo 📊 Проверка файлов...
if not exist app.py (
    echo ❌ app.py не найден!
    pause
    exit /b 1
)

if not exist cloudflared.exe (
    echo ❌ cloudflared.exe не найден!
    echo 💡 Скачайте с: https://github.com/cloudflare/cloudflared/releases/latest
    pause
    exit /b 1
)

echo ✅ Все файлы найдены

echo.
echo 🚀 Запуск Flask приложения...
echo 💡 Оставьте это окно открытым
echo.

python app.py

pause 