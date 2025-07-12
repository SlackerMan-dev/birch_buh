#!/bin/bash

# Скрипт первоначальной настройки сервера Yandex Cloud
# Запускать на сервере после создания ВМ

echo "🔧 Начинаем настройку сервера..."

# 1. Обновление системы
echo "📦 Обновляем систему..."
sudo apt update && sudo apt upgrade -y

# 2. Установка необходимого ПО
echo "🐍 Устанавливаем Python и зависимости..."
sudo apt install python3 python3-pip python3-venv git nginx supervisor ufw -y

# 3. Создание пользователя для приложения
echo "👤 Создаем пользователя webapp..."
sudo useradd -m -s /bin/bash webapp
sudo usermod -aG sudo webapp

# 4. Настройка SSH для пользователя webapp
echo "🔑 Настраиваем SSH доступ..."
sudo mkdir -p /home/webapp/.ssh
sudo cp /home/ubuntu/.ssh/authorized_keys /home/webapp/.ssh/
sudo chown -R webapp:webapp /home/webapp/.ssh
sudo chmod 700 /home/webapp/.ssh
sudo chmod 600 /home/webapp/.ssh/authorized_keys

# 5. Создание директорий для проекта
echo "📁 Создаем директории проекта..."
sudo mkdir -p /var/www/accounting
sudo chown webapp:webapp /var/www/accounting

# 6. Создание лог-директорий
echo "📝 Создаем лог-директории..."
sudo mkdir -p /var/log/gunicorn
sudo chown webapp:webapp /var/log/gunicorn

# 7. Настройка файрвола
echo "🔥 Настраиваем файрвол..."
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

echo "✅ Настройка сервера завершена!"
echo "🚀 Сервер готов к деплою приложения" 