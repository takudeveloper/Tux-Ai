#!/bin/bash
# TUX AI - Скрипт запуска всех сервисов

echo "🐧 Запуск TUX AI System..."

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не установлен"
    exit 1
fi

# Создание виртуального окружения (опционально)
if [ ! -d "venv" ]; then
    echo "📦 Создаю виртуальное окружение..."
    python3 -m venv venv
fi

# Активация виртуального окружения
source venv/bin/activate

# Установка зависимостей
echo "📥 Проверяю зависимости..."
pip install -r requirements.txt

# Запуск основной системы
echo "🚀 Запускаю TUX AI..."
python LAUNCH.py

# Если произошла ошибка
if [ $? -ne 0 ]; then
    echo "❌ Ошибка запуска"
    echo "🔄 Попробуйте запустить setup_environment.py"
    python setup_environment.py
fi