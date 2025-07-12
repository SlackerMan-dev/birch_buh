#!/usr/bin/env python3
"""
Скрипт для запуска Flask приложения с Cloudflare Tunnel
Бесплатная альтернатива ngrok с постоянным доменом
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_requirements():
    try:
        import requests
        from cryptography import x509
    except ImportError:
        print("Установка необходимых зависимостей...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "cryptography"])

def download_cloudflare_cert():
    import requests
    
    cert_dir = Path("certs")
    cert_dir.mkdir(exist_ok=True)
    
    cert_path = cert_dir / "cloudflare-origin.pem"
    if not cert_path.exists():
        print("Загрузка корневого сертификата Cloudflare...")
        response = requests.get("https://developers.cloudflare.com/cloudflare-one/static/documentation/connections/Cloudflare_CA.pem")
        cert_path.write_bytes(response.content)
    
    return cert_path

def create_config():
    config = """ingress:
  - hostname: "*"
    service: http://localhost:5000
    originRequest:
      noTLSVerify: true
      connectTimeout: 30s
      tlsTimeout: 30s
      tcpKeepAlive: 30s
      keepAliveConnections: 100
      keepAliveTimeout: 90s
      noHappyEyeballs: true
  - service: http_status:404

retries: 5
grace-period: 30s
protocol: h2mux
compression-quality: 0
edge-ip-version: 4
metrics-update-freq: 5s
"""
    
    config_path = Path("config.yml")
    if not config_path.exists():
        print("Создание конфигурации туннеля...")
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config)

def main():
    print("Настройка Cloudflare туннеля...")
    
    # Проверка зависимостей
    check_requirements()
    
    # Загрузка сертификата
    cert_path = download_cloudflare_cert()
    
    # Создание конфигурации
    create_config()
    
    # Создание bat-файла для запуска
    bat_content = f"""@echo off
echo Starting Cloudflare tunnel...

set TUNNEL_EDGE_IP_VERSION=4
set TUNNEL_ORIGIN_CERT=certs/cert.pem
set TUNNEL_METRICS=localhost:20241
set TUNNEL_LOGLEVEL=debug
set TUNNEL_TRANSPORT_LOGLEVEL=debug
set TUNNEL_GRACE_PERIOD=30s
set TUNNEL_RETRIES=5

cloudflared.exe tunnel --url http://localhost:5000 ^
    --no-autoupdate ^
    --origin-ca-pool "{cert_path}" ^
    --protocol h2mux ^
    --edge-ip-version 4 ^
    --retries 5 ^
    --grace-period 30s ^
    --metrics localhost:20241 ^
    --loglevel debug ^
    --transport-loglevel debug
pause
"""
    
    with open("start_cloudflare.bat", "w", encoding='utf-8') as f:
        f.write(bat_content)
    
    print("\nНастройка завершена!")
    print("1. Запустите Flask приложение")
    print("2. Запустите start_cloudflare.bat")

if __name__ == "__main__":
    main() 