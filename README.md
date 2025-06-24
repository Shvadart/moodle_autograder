# 🚀 Moodle Evaluator - AI-powered Assessment System

[![Docker](https://img.shields.io/badge/Docker-✓-blue?logo=docker)](https://www.docker.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-green?logo=openai)](https://openai.com/)
[![Moodle](https://img.shields.io/badge/Moodle-✓-orange?logo=moodle)](https://moodle.org/)

Система автоматической проверки ответов студентов в Moodle с использованием искусственного интеллекта (OpenAI GPT-4).

## 📑 Содержание

- [🖥 Минимальные системные требования](#-минимальные-системные-требования)
- [✨ Основные возможности](#-основные-возможности)
- [📦 Требования](#-требования)
- [🚀 Быстрый старт](#-быстрый-старт)
  - [1. Клонирование репозитория](#1-клонирование-репозитория)
  - [2. Настройка окружения](#2-настройка-окружения)
  - [2.1 Подключение к существующей базе Moodle](#21-подключение-системы-автоматизированной-оценки-к-уже-существующей-базе-данных-moodle)
  - [3. Запуск системы](#3-запуск-системы)
  - [4. Доступ к сервисам](#4-доступ-к-сервисам)
- [🌐 Использование веб-интерфейса](#-использование-веб-интерфейса)
- [⌨️ Использование CLI интерфейса](#использование-cli-интерфейса)
- [🛠 Управление системой](#-управление-системой)


## 🖥 Минимальные системные требования

| Компонент       | Требования                          |
|-----------------|-------------------------------------|
| ОС             | Linux (Ubuntu 20.04+, Debian 10+), Windows 10/11, macOS 10.15+ |
| CPU            | 2 ядра (рекомендуется 4+)          |
| RAM            | 4 GB (рекомендуется 8 GB+)         |
| Дисковое пространство | 10 GB (плюс место для базы данных Moodle) |
| Docker         | Версия 20.10.0+                    |
| Docker Compose | Версия 2.0.0+                      |

## ✨ Основные возможности

- ✅ **Автоматическая проверка** ответов на вопросы типа "эссе"
- ⚡️ **Интеграция с OpenAI GPT-4** для интеллектуальной оценки
- 🌐 **Веб-интерфейс** для управления процессом проверки
- ⌨️ **Командный интерфейс** (CLI)
- 🐳 **Полная Docker-поддержка** для простого развертывания
- 📊 **Мгновенное обновление оценок** в Moodle

## 📦 Требования

1. [Docker](https://www.docker.com/products/docker-desktop/)
> [!TIP]
> При установке docker на сервер Linux без графического интерфейса ознакомьтесь с этой статьёй [Ссылка](https://www.dmosk.ru/miniinstruktions.php?mini=docker-install-linux) 
2. API-ключ OpenAI ([получить здесь](https://proxyapi.ru/))

## 🚀 Быстрый старт

### 1. Клонирование репозитория
```bash
git clone https://github.com/Shvadart/moodle_autograder.git
cd moodle_autograder
```
### 2. Настройка окружения
```bash
cp .exampleenv .env
nano .env  # Редактируем файл
```
Пример содержимого .env:
```bash
# Moodle Database Settings
DB_HOST=your-db-host
DB_USER=your-db-user
DB_PASSWORD=your-db-password
DB_NAME=your-db-name

# OpenAI Settings
OPENAI_API_KEY=your-api-key-here
OPENAI_BASE_URL=https://api.proxyapi.ru/openai/v1
```
#### 2.1 Подключение системы автоматизированной оценки к уже существующей базе данных Moodle
Замените содержимое файла docker-compose.yml на указанное ниже, при чем не забудьте в MYSQL_HOST ввести IP адрес сервера, на котором расположена БД, а также порт MYSQL_PORT.

> [!IMPORTANT]
> Текущая реализация программы работает с MariaDB, для других СУБД возможно будет необходимо изменить систему подключения к базе данных в модуле moodle_db.py.

```bash
version: '3'

services:
  evaluator:
    build:
      context: .
    container_name: moodle_evaluator
    ports:
      - "5000:5000"  # Веб-интерфейс проверки
    env_file:
      - .env
    environment:
      MYSQL_HOST: # Укажите IP сервера 
      MYSQL_PORT: 3306
      MYSQL_USER: moodleuser
      MYSQL_PASSWORD: moodlepass
      MYSQL_DATABASE: moodle

  evaluator-cli:
    build:
      context: .
    container_name: moodle_evaluator_cli
    env_file:
      - .env
    environment:
      MYSQL_HOST: # Укажите IP сервера
      MYSQL_PORT: 3306
      MYSQL_USER: moodleuser
      MYSQL_PASSWORD: moodlepass
      MYSQL_DATABASE: moodle
    command: ["python", "/app/cli_interface.py"]
    tty: true
    stdin_open: true
    volumes:
      - ./app:/app
```
### 3. Запуск системы
```bash
docker-compose up -d --build
```

### 4. Доступ к сервисам
Сервис	URL 
- Moodle	http://localhost:8080 
- Веб-интерфейс	http://localhost:5000 
- База данных	moodle_db:3306 

Если вы выполнили пункт 2.1, то Moodle	http://localhost:8080 вам будет не доступен


## 🌐 Использование веб-интерфейса
После запуска откройте http://localhost:5000: 

Панель управления проверкой:
- Установите интервал проверки (по умолчанию 30 сек) 
- Запустите/остановите автоматическую проверку 

Управление эталонными ответами:
- Система автоматически покажет вопросы без эталонных ответов 
- Для каждого вопроса без эталонного ответа: 
    - Введите правильный ответ в текстовое поле 
    - Нажмите "Сохранить в graderinfo" 
    - Система сохранит ответ в базу данных Moodle 

## Использование CLI интерфейса
Чтобы вызвать командный интерфейс, в директории необходимо выполнить команду
```bash
docker-compose run --rm evaluator-cli
```
Пример работы с CLI:
```bash
=== Moodle Evaluator CLI ===
Статус: Проверка не активна
Интервал: 30 сек

Выберите действие:
> Запустить проверку
  Изменить интервал проверки
  Проверить наличие эталонных ответов
  Выход
```
Основные команды:
- Запустить/остановить проверку: Включает или выключает фоновую проверку 
- Изменить интервал: Устанавливает интервал между проверками (в секундах) 
- Проверить эталонные ответы: Показывает вопросы без правильных ответов и позволяет их добавить

## 🛠 Управление системой
Полезные команды
```bash
# Запуск системы
docker-compose up -d --build

# Остановка системы
docker-compose down
```
