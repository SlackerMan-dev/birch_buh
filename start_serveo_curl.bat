@echo off
echo Starting Serveo tunnel with curl...

:: Используем curl для создания туннеля
curl -s -N -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Sec-WebSocket-Key: SGVsbG8sIHdvcmxkIQ==" -H "Sec-WebSocket-Version: 13" https://serveo.net/ssh

pause
