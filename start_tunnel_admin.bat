@echo off
chcp 65001 > nul

NET SESSION >nul 2>&1
if %errorLevel% == 0 (
    echo ✓ Запущено с правами администратора
) else (
    echo ❌ Этот скрипт требует прав администратора
    echo Пожалуйста, запустите от имени администратора
    pause
    exit /b 1
)

echo Проверка наличия сертификатов...
if not exist "certs\cert.pem" (
    echo ❌ Сертификаты не найдены
    echo Запустите setup_cloudflare_cert.py для создания сертификатов
    pause
    exit /b 1
)
echo ✓ Сертификаты найдены

echo Настройка брандмауэра...
netsh advfirewall firewall add rule name="Cloudflared Tunnel" dir=in action=allow program="%~dp0cloudflared.exe" enable=yes > nul
netsh advfirewall firewall add rule name="Cloudflared Tunnel Out" dir=out action=allow program="%~dp0cloudflared.exe" enable=yes > nul
echo ✓ Правила брандмауэра добавлены

echo Проверка сетевого подключения...
ping -4 1.1.1.1 -n 1 > nul
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
    echo ℹ️ Порт 5000 активен
) else (
    echo ❌ Предупреждение: Порт 5000 не активен
    echo Убедитесь, что Flask-приложение запущено
    pause
)

echo.
echo Запуск Cloudflare туннеля...
echo Для остановки нажмите Ctrl+C
echo.

cloudflared.exe tunnel --config config.yml --origincert certs/cert.pem 