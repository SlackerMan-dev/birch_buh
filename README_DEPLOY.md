# 🚀 Инструкция по деплою в Yandex Cloud

## 📋 Что я уже сделал автоматически:

✅ **Создал файлы для продакшена:**
- `gunicorn_config.py` - конфигурация Gunicorn сервера
- `wsgi.py` - WSGI файл для запуска приложения
- `deploy.sh` - скрипт автоматического деплоя
- `setup_server.sh` - скрипт настройки сервера
- `check_deployment.py` - проверка готовности проекта
- Обновил `requirements.txt` с Gunicorn

---

## 🎯 Что вам нужно сделать:

### Шаг 1: Проверка проекта
```bash
python check_deployment.py
```

### Шаг 2: Создание ВМ в Yandex Cloud

1. **Зайдите в [cloud.yandex.ru](https://cloud.yandex.ru/)**
2. **Создайте платежный аккаунт** (если еще не создан)
3. **Создайте облачный проект** с названием "Бухгалтерия"
4. **Создайте ВМ:**
   - **Имя:** `accounting-server`
   - **ОС:** Ubuntu 22.04 LTS
   - **Платформа:** Intel Ice Lake
   - **Ядра:** 2
   - **RAM:** 4 ГБ
   - **Диск:** 50 ГБ SSD
   - **Публичный IP:** ✅ включите
   - **SSH-ключ:** создайте новый

### Шаг 3: Настройка сервера

**Подключитесь к серверу:**
```bash
ssh ubuntu@ВАШ_IP_АДРЕС
```

**Скопируйте и запустите скрипт настройки:**
```bash
# Скопируйте setup_server.sh на сервер
scp setup_server.sh ubuntu@ВАШ_IP_АДРЕС:~/

# На сервере запустите:
chmod +x setup_server.sh
./setup_server.sh
```

### Шаг 4: Деплой приложения

**Сделайте скрипт деплоя исполняемым:**
```bash
chmod +x deploy.sh
```

**Запустите деплой:**
```bash
./deploy.sh ВАШ_IP_АДРЕС
```

### Шаг 5: Проверка работы

**Проверьте статус сервисов:**
```bash
ssh ubuntu@ВАШ_IP_АДРЕС "sudo systemctl status accounting"
ssh ubuntu@ВАШ_IP_АДРЕС "sudo systemctl status nginx"
```

**Откройте сайт:**
```
http://ВАШ_IP_АДРЕС
```

---

## 🌐 Настройка домена (опционально)

### 1. Покупка домена
- Купите домен у любого регистратора (reg.ru, nic.ru)

### 2. Настройка DNS
- Создайте A-запись на IP вашего сервера

### 3. Настройка SSL
```bash
ssh ubuntu@ВАШ_IP_АДРЕС
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d ваш_домен.com
```

---

## 🔧 Управление приложением

### Перезапуск приложения:
```bash
ssh ubuntu@ВАШ_IP_АДРЕС "sudo systemctl restart accounting"
```

### Просмотр логов:
```bash
ssh ubuntu@ВАШ_IP_АДРЕС "sudo journalctl -u accounting -f"
```

### Обновление кода:
```bash
# Скопируйте новые файлы
scp -r ./* ubuntu@ВАШ_IP_АДРЕС:/var/www/accounting/
# Перезапустите приложение
ssh ubuntu@ВАШ_IP_АДРЕС "sudo systemctl restart accounting"
```

---

## 💰 Стоимость

**Примерная стоимость в месяц:**
- **ВМ (2 ядра, 4 ГБ RAM, 50 ГБ SSD):** ~800-1200 ₽
- **Домен:** ~100-200 ₽/год
- **Итого:** ~800-1200 ₽/месяц

---

## 🆘 Устранение проблем

### Если приложение не запускается:
```bash
ssh ubuntu@ВАШ_IP_АДРЕС "sudo journalctl -u accounting -n 50"
```

### Если сайт недоступен:
```bash
ssh ubuntu@ВАШ_IP_АДРЕС "sudo systemctl status nginx"
ssh ubuntu@ВАШ_IP_АДРЕС "curl http://localhost:8000"
```

### Если база данных недоступна:
```bash
ssh ubuntu@ВАШ_IP_АДРЕС "sudo -u webapp /var/www/accounting/venv/bin/python3 /var/www/accounting/check_db.py"
```

---

## 📞 Поддержка

**Если что-то не работает:**
1. Проверьте логи: `sudo journalctl -u accounting -f`
2. Проверьте статус сервисов: `sudo systemctl status accounting nginx`
3. Проверьте файрвол: `sudo ufw status`

**Готово!** Ваше приложение будет доступно по IP адресу сервера. 