@echo off
echo Opening port 8000 in Windows Firewall...

:: Открываем порт 8000 для входящих соединений
netsh advfirewall firewall add rule name="Simple HTTP Server" dir=in action=allow protocol=TCP localport=8000

echo Port 8000 opened successfully!
pause
