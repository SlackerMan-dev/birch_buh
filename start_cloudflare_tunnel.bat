@echo off
echo 🌐 Запуск Cloudflare Tunnel
echo ============================

echo 📊 Проверка cloudflared...
if not exist cloudflared.exe (
    echo ❌ cloudflared.exe не найден!
    echo 💡 Скачайте с: https://github.com/cloudflare/cloudflared/releases/latest
    pause
    exit /b 1
)

echo 🚀 Запуск туннеля...
echo.
echo 📱 Туннель создается...
echo 💡 URL будет показан ниже
echo.

cloudflared.exe tunnel --url http://localhost:5000

pause 