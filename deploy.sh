#!/bin/bash

# Скрипт автоматического деплоя на Yandex Cloud
# Использование: ./deploy.sh IP_АДРЕС_СЕРВЕРА

if [ -z "$1" ]; then
    echo "Использование: ./deploy.sh IP_АДРЕС_СЕРВЕРА"
    echo "Пример: ./deploy.sh 51.250.123.45"
    exit 1
fi

SERVER_IP=$1
PROJECT_DIR="/var/www/accounting"

echo "🚀 Начинаем деплой на сервер $SERVER_IP..."

# 1. Создание директорий на сервере
echo "📁 Создаем директории..."
ssh ubuntu@$SERVER_IP "sudo mkdir -p $PROJECT_DIR && sudo chown ubuntu:ubuntu $PROJECT_DIR"

# 2. Копирование файлов проекта
echo "📂 Копируем файлы проекта..."
scp -r ./* ubuntu@$SERVER_IP:$PROJECT_DIR/

# 3. Копирование базы данных
echo "🗄️ Копируем базу данных..."
scp arbitrage_reports.db ubuntu@$SERVER_IP:$PROJECT_DIR/instance/

# 4. Настройка прав доступа
echo "🔐 Настраиваем права доступа..."
ssh ubuntu@$SERVER_IP "sudo chown -R webapp:webapp $PROJECT_DIR && sudo chmod -R 755 $PROJECT_DIR"

# 5. Установка зависимостей
echo "🐍 Устанавливаем Python зависимости..."
ssh ubuntu@$SERVER_IP "cd $PROJECT_DIR && sudo -u webapp python3 -m venv venv && sudo -u webapp venv/bin/pip install -r requirements.txt"

# 6. Создание директорий для загрузок
echo "📁 Создаем директории для загрузок..."
ssh ubuntu@$SERVER_IP "sudo -u webapp mkdir -p $PROJECT_DIR/uploads"

# 7. Настройка systemd сервиса
echo "⚙️ Настраиваем systemd сервис..."
ssh ubuntu@$SERVER_IP "sudo tee /etc/systemd/system/accounting.service > /dev/null << 'EOF'
[Unit]
Description=Accounting Web Application
After=network.target

[Service]
User=webapp
Group=webapp
WorkingDirectory=$PROJECT_DIR
Environment=\"PATH=$PROJECT_DIR/venv/bin\"
Environment=\"FLASK_ENV=production\"
Environment=\"DATABASE_URL=sqlite:///instance/arbitrage_reports.db\"
ExecStart=$PROJECT_DIR/venv/bin/gunicorn --config $PROJECT_DIR/gunicorn_config.py wsgi:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF"

# 8. Создание лог-директорий
echo "📝 Создаем лог-директории..."
ssh ubuntu@$SERVER_IP "sudo mkdir -p /var/log/gunicorn && sudo chown webapp:webapp /var/log/gunicorn"

# 9. Настройка Nginx
echo "🌐 Настраиваем Nginx..."
ssh ubuntu@$SERVER_IP "sudo tee /etc/nginx/sites-available/accounting > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;

    access_log /var/log/nginx/accounting_access.log;
    error_log /var/log/nginx/accounting_error.log;

    client_max_body_size 16M;

    location /static {
        alias $PROJECT_DIR/static;
        expires 30d;
        add_header Cache-Control \"public, immutable\";
    }

    location /uploads {
        alias $PROJECT_DIR/uploads;
        expires 1d;
        add_header Cache-Control \"public\";
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF"

# 10. Активация Nginx конфигурации
echo "🔗 Активируем Nginx конфигурацию..."
ssh ubuntu@$SERVER_IP "sudo ln -sf /etc/nginx/sites-available/accounting /etc/nginx/sites-enabled/ && sudo rm -f /etc/nginx/sites-enabled/default"

# 11. Настройка файрвола
echo "🔥 Настраиваем файрвол..."
ssh ubuntu@$SERVER_IP "sudo ufw allow 22/tcp && sudo ufw allow 80/tcp && sudo ufw allow 443/tcp && sudo ufw --force enable"

# 12. Запуск сервисов
echo "🚀 Запускаем сервисы..."
ssh ubuntu@$SERVER_IP "sudo systemctl daemon-reload && sudo systemctl enable accounting && sudo systemctl start accounting && sudo systemctl restart nginx"

echo "✅ Деплой завершен!"
echo "🌐 Сайт доступен по адресу: http://$SERVER_IP"
echo "📊 Статус сервисов:"
ssh ubuntu@$SERVER_IP "sudo systemctl status accounting --no-pager -l" 