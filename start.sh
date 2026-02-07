#!/usr/bin/env bash

# Имя сервиса
SERVICE_NAME=duplicate-message-bot.service

# Запуск остановленного сервиса
sudo systemctl restart $SERVICE_NAME
sudo systemctl enable $SERVICE_NAME