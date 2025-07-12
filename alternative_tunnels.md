# 🌐 Альтернативные способы доступа к приложению

## 1. **Cloudflare Tunnel** (Бесплатно)
```bash
# Скачайте cloudflared.exe и запустите:
cloudflared.exe tunnel --url http://localhost:5000
```

## 2. **LocalTunnel** (Бесплатно)
```bash
# Установите Node.js, затем:
npm install -g localtunnel
lt --port 5000
```

## 3. **Serveo** (Бесплатно)
```bash
# Если у вас есть SSH:
ssh -R 80:localhost:5000 serveo.net
```

## 4. **Локальная сеть** (Самый простой)
```bash
# Запустите start_local_network.bat
# Затем найдите ваш IP: ipconfig
# Поделитесь ссылкой: http://YOUR_IP:5000
```

## 5. **Роутер + Порт-форвардинг**
1. Настройте роутер для перенаправления порта 5000
2. Узнайте внешний IP: whatismyipaddress.com
3. Поделитесь ссылкой: http://YOUR_EXTERNAL_IP:5000

## 🎯 Рекомендация
Начните с **локальной сети** - это самый простой способ для офиса. 