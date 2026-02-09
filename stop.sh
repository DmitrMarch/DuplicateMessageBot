#!/usr/bin/env bash

# Имя сервиса
SERVICE_NAME=duplicate-message-bot.service

# Остановка сервиса
systemctl stop $SERVICE_NAME
systemctl disable $SERVICE_NAME