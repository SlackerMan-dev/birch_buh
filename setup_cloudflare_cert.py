import os
from pathlib import Path
import subprocess
import sys

def install_required_packages():
    print("📦 Установка необходимых пакетов...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "cryptography"])
        return True
    except Exception as e:
        print(f"❌ Ошибка при установке пакетов: {str(e)}")
        return False

def setup_certificates():
    print("🔧 Настройка сертификатов для Cloudflare...")
    
    # Проверяем наличие необходимых пакетов
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        import datetime
    except ImportError:
        if not install_required_packages():
            return None, None
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        import datetime
    
    # Создаем директорию для сертификатов
    cert_dir = Path("certs")
    cert_dir.mkdir(exist_ok=True)
    
    # Пути к файлам сертификатов
    cert_path = cert_dir / "cert.pem"
    key_path = cert_dir / "key.pem"
    
    try:
        # Генерируем закрытый ключ
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        
        # Создаем сертификат
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, u"localhost")
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(u"localhost")
            ]),
            critical=False
        ).sign(private_key, hashes.SHA256())
        
        # Сохраняем сертификат
        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        # Сохраняем закрытый ключ
        with open(key_path, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        print("✓ Сертификаты созданы")
        return str(cert_path), str(key_path)
        
    except Exception as e:
        print(f"❌ Ошибка при создании сертификатов: {str(e)}")
        return None, None

def create_config(cert_path, key_path):
    print("\n⚙️ Создание конфигурации Cloudflare...")
    
    config = f"""url: http://localhost:5000
protocol: http2
loglevel: debug
transport-loglevel: debug
originRequest:
  noTLSVerify: true
  connectTimeout: 30s
  tlsTimeout: 30s
ingress:
  - hostname: "*"
    service: http://localhost:5000
    originRequest:
      noTLSVerify: true
      connectTimeout: 30s
      tlsTimeout: 30s
      cert: {cert_path}
      key: {key_path}
metrics: 127.0.0.1:20241
disableChunkedEncoding: true
noAutoupdate: true
disableIPv6: true"""
    
    try:
        with open("config.yml", "w") as f:
            f.write(config)
        print("✓ Конфигурация создана")
        return True
    except Exception as e:
        print(f"❌ Ошибка при создании конфигурации: {str(e)}")
        return False

if __name__ == "__main__":
    cert_path, key_path = setup_certificates()
    if cert_path and key_path:
        if create_config(cert_path, key_path):
            print("\n✅ Настройка завершена успешно")
            print("Теперь вы можете запустить туннель через start_tunnel_admin.bat")
        else:
            print("\n❌ Не удалось создать конфигурацию")
    else:
        print("\n❌ Не удалось создать сертификаты")
    
    input("\nНажмите Enter для завершения...") 