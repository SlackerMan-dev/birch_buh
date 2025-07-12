import http.server
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
        print("💡 Для доступа из интернета:")
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
