@echo off
echo 🔧 Установка зависимостей для функции загрузки файлов...
echo.

echo 📦 Устанавливаю pandas...
pip install pandas
if errorlevel 1 (
    echo ❌ Ошибка установки pandas
    pause
    exit /b 1
)

echo 📦 Устанавливаю openpyxl...
pip install openpyxl
if errorlevel 1 (
    echo ❌ Ошибка установки openpyxl
    pause
    exit /b 1
)

echo 📦 Устанавливаю xlrd...
pip install xlrd
if errorlevel 1 (
    echo ❌ Ошибка установки xlrd
    pause
    exit /b 1
)

echo.
echo 🎉 Все зависимости успешно установлены!
echo Теперь можно запустить сервер командой: python app.py
echo.
pause 