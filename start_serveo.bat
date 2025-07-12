@echo off
echo Starting Serveo tunnel...

:: Используем SSH для создания туннеля
ssh -R 80:localhost:5000 serveo.net

pause
