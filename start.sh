#!/usr/bin/env bash

# Имя сервиса
SERVICE_NAME=duplicate-message-bot.service

# Запуск остановленного сервиса
systemctl restart $SERVICE_NAME
systemctl enable $SERVICE_NAME