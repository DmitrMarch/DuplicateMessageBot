#!/usr/bin/env bash

# Имя сервиса
SERVICE_NAME=duplicate-message-bot.service

# Остановка сервиса
sudo systemctl stop $SERVICE_NAME
sudo systemctl disable $SERVICE_NAME