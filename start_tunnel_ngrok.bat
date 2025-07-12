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

echo Настройка брандмауэра...
netsh advfirewall firewall add rule name="ngrok Tunnel" dir=in action=allow program="%~dp0ngrok.exe" enable=yes > nul
netsh advfirewall firewall add rule name="ngrok Tunnel Out" dir=out action=allow program="%~dp0ngrok.exe" enable=yes > nul
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
echo Запуск ngrok туннеля...
echo Для остановки нажмите Ctrl+C
echo.

ngrok.exe http --log=stdout 5000 