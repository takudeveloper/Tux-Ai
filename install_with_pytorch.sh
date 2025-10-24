#!/bin/bash
# Установка TUX AI с PyTorch для Arch Linux

echo "🐧 Установка TUX AI с нейронной сетью..."
echo "==========================================="

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не установлен"
    sudo pacman -S python --noconfirm
fi

# Установка системных зависимостей
echo "📦 Устанавливаю системные зависимости..."
sudo pacman -S --noconfirm \
    python-pip \
    python-virtualenv \
    tesseract \
    tesseract-data-eng \
    tesseract-data-rus \
    poppler \
    git \
    base-devel \
    opencv \
    python-opencv

# Создание виртуального окружения
echo "🐍 Создаю виртуальное окружение..."
python -m venv tux_ai_venv

# Активация venv
echo "🔧 Активирую виртуальное окружение..."
source tux_ai_venv/bin/activate

# Обновление pip
echo "🔄 Обновляю pip..."
pip install --upgrade pip

# Установка PyTorch и зависимостей
echo "🧠 Устанавливаю PyTorch и зависимости..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Установка остальных зависимостей
pip install textual rich transformers requests pillow numpy opencv-python

echo ""
echo "🎉 Установка завершена!"
echo "==========================================="
echo "🚀 Для запуска нейронной сети:"
echo "   python LAUNCH.py"
echo "   (выберите вариант 1 или 4)"
echo ""
echo "🧠 Демонстрация нейронной сети:"
echo "   python -c \"from src.core.tux_neural_network import demonstrate_tux_ai; demonstrate_tux_ai()\""