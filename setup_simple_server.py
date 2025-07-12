import os
import sys
import subprocess
from pathlib import Path

def create_simple_server():
    """Создает простой HTTP сервер"""
    server_script = """import http.server
import socketserver
import socket
import threading
import webbrowser
from pathlib import Path

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def start_server():
    PORT = 8000
    local_ip = get_local_ip()
    
    # Создаем простую HTML страницу для теста
    html_content = '''
<!DOCTYPE html>
<html>
<head>
    <title>Тест сервера</title>
    <meta charset="utf-8">
</head>
<body>
    <h1>Сервер работает!</h1>
    <p>Если вы видите эту страницу, сервер доступен извне.</p>
    <p>Локальный IP: {ip}</p>
    <p>Порт: {port}</p>
</body>
</html>
'''.format(ip=local_ip, port=PORT)
    
    # Сохраняем HTML файл
    with open("test.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    # Запускаем сервер
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print(f"🚀 Сервер запущен!")
        print(f"📱 Локальный доступ: http://localhost:{PORT}")
        print(f"🌐 Внешний доступ: http://{local_ip}:{PORT}")
        print(f"📄 Тестовая страница: http://{local_ip}:{PORT}/test.html")
        print("\n💡 Для доступа из интернета:")
        print("1. Откройте порт 8000 в брандмауэре Windows")
        print("2. Настройте проброс портов в роутере")
        print("3. Используйте ваш внешний IP")
        
        # Открываем браузер
        try:
            webbrowser.open(f"http://localhost:{PORT}/test.html")
        except:
            pass
        
        httpd.serve_forever()

if __name__ == "__main__":
    start_server()
"""
    
    with open("simple_server.py", "w", encoding="utf-8") as f:
        f.write(server_script)
    
    print("✅ Простой HTTP сервер создан")

def create_bat_file():
    """Создает bat-файл для запуска"""
    bat_content = """@echo off
echo Starting simple HTTP server...

:: Запускаем простой сервер
python simple_server.py

pause
"""
    
    with open("start_simple_server.bat", "w", encoding="utf-8") as f:
        f.write(bat_content)
    
    print("✅ Файл start_simple_server.bat создан")

def create_firewall_script():
    """Создает скрипт для открытия порта в брандмауэре"""
    firewall_script = """@echo off
echo Opening port 8000 in Windows Firewall...

:: Открываем порт 8000 для входящих соединений
netsh advfirewall firewall add rule name="Simple HTTP Server" dir=in action=allow protocol=TCP localport=8000

echo Port 8000 opened successfully!
pause
"""
    
    with open("open_firewall.bat", "w", encoding="utf-8") as f:
        f.write(firewall_script)
    
    print("✅ Файл open_firewall.bat создан")

def main():
    print("🚀 Настройка простого HTTP сервера")
    print("=" * 40)
    
    # Создаем сервер
    create_simple_server()
    
    # Создаем bat-файл
    create_bat_file()
    
    # Создаем скрипт для брандмауэра
    create_firewall_script()
    
    print("\n✅ Настройка завершена!")
    print("\n📋 Инструкция:")
    print("1. Запустите open_firewall.bat (открыть порт)")
    print("2. Запустите start_simple_server.bat")
    print("3. Получите ваш внешний IP на whatismyipaddress.com")
    print("4. Откройте http://ВАШ_ВНЕШНИЙ_IP:8000")
    print("\n💡 Преимущества:")
    print("- Не требует внешних сервисов")
    print("- Полный контроль")
    print("- Работает в России")
    print("- Бесплатно")

if __name__ == "__main__":
    main() 