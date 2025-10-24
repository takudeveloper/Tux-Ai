#!/bin/bash
# TUX AI - Скрипт запуска для Linux/Arch Linux

echo "🐧 Запуск TUX AI System для Arch Linux..."

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не установлен"
    echo "📥 Установите: sudo pacman -S python"
    exit 1
fi

# Активация виртуального окружения
if [ -d "venv" ]; then
    echo "🔧 Активирую виртуальное окружение..."
    source venv/bin/activate
else
    echo "🛠️ Виртуальное окружение не найдено"
    echo "🚀 Создаю виртуальное окружение..."
    python3 -m venv venv
    source venv/bin/activate
    
    echo "📦 Устанавливаю зависимости..."
    pip install --upgrade pip
    pip install torch transformers textual rich fastapi uvicorn aiohttp requests
fi

# Запуск основной системы
echo "🚀 Запускаю TUX AI..."
python3 LAUNCH.py

# Обработка ошибок
if [ $? -ne 0 ]; then
    echo "❌ Ошибка запуска"
    echo "🔄 Попробуйте запустить setup_environment.py"
    python3 setup_environment.py
fi