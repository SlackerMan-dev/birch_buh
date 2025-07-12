@echo off
chcp 65001 > nul

echo Проверка сетевого подключения...
ping 1.1.1.1 -n 1 > nul
if errorlevel 1 (
    echo ❌ Ошибка: Нет подключения к интернету
    echo Проверьте ваше интернет-соединение
    pause
    exit /b 1
)
echo ✓ Подключение к интернету работает

echo Проверка доступности порта 5000...
netstat -an | find "5000" > nul
if not errorlevel 1 (
    echo ❌ Предупреждение: Порт 5000 уже используется
    echo Убедитесь, что Flask-приложение запущено
)

echo Проверка брандмауэра...
netsh advfirewall show currentprofile state | find "ON" > nul
if not errorlevel 1 (
    echo ℹ️ Брандмауэр Windows включен
    echo Если возникнут проблемы с подключением, возможно потребуется добавить правило в брандмауэр
)

echo.
echo Запуск Cloudflare туннеля...
echo Для остановки нажмите Ctrl+C
echo.

cloudflared.exe tunnel --config config.yml
