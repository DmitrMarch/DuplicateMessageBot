#!/usr/bin/env bash

# Имя сервиса
SERVICE_NAME=duplicatemessagebot.service

# ----------------------------
# Обновление системы и зависимостей
# ----------------------------
echo "Обновление системы и установка нужных пакетов"
sudo apt update -y
sudo apt install -y python3 python3-venv python3-pip

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
sudo systemctl daemon-reload
sudo systemctl restart $SERVICE_NAME
sudo systemctl enable $SERVICE_NAME

echo "Deploy завершён"