#!/usr/bin/env bash
set -e

# Логирование сообщений и ошибок
LOGFILE=deploy.log
exec >> "$LOGFILE" 2>&1

echo "==== Deploy start: $(date) ===="

# Имя сервиса
SERVICE_NAME=duplicate-message-bot.service

# ----------------------------
# Настройка виртуального окружения
# ----------------------------
if [ ! -d "venv" ]; then
    echo "Создаём виртуальное окружение"
    python3 -m venv venv
fi

# Активируем виртуальное окружение
source venv/bin/activate

# ----------------------------
# Установка зависимостей
# ----------------------------
echo "Установка зависимостей"
pip install --upgrade pip
pip install -r requirements.txt

# ----------------------------
# Перезапуск systemd сервиса
# ----------------------------
echo "Перезапуск systemd сервиса"
systemctl restart $SERVICE_NAME

echo "Deploy завершён"
echo "==== Deploy end: $(date) ===="