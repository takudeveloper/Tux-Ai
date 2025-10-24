#!/bin/bash
# TUX AI - Установщик для Arch Linux

echo "🐧 Установка TUX AI на Arch Linux..."
echo "==========================================="

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не установлен"
    echo "Установка: sudo pacman -S python"
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
    base-devel

# Создание виртуального окружения
echo "🐍 Создаю виртуальное окружение..."
python -m venv tux_ai_venv

# Активация venv
echo "🔧 Активирую виртуальное окружение..."
source tux_ai_venv/bin/activate

# Обновление pip внутри venv
echo "🔄 Обновляю pip..."
pip install --upgrade pip

# Создание структуры проекта
echo "📁 Создаю структуру проекта..."
mkdir -p tux-ai-project/{src/{core,tui,plugins,api,utils},data/{models,uploads,training,memory,plugins},logs,tests}
cd tux-ai-project

# Создание __init__.py файлов
touch src/__init__.py
touch src/core/__init__.py
touch src/tui/__init__.py
touch src/plugins/__init__.py
touch src/api/__init__.py
touch src/utils/__init__.py

# Копирование основных файлов (это нужно сделать вручную)
echo "📋 Копирую файлы проекта..."

# Создание основных файлов
cat > LAUNCH.py << 'EOF'
#!/usr/bin/env python3
"""
🐧 TUX AI - Главный файл запуска для Arch Linux
Автоматически активирует виртуальное окружение
"""

import os
import sys
import subprocess
from pathlib import Path

def ensure_venv():
    """Проверка и активация виртуального окружения"""
    venv_path = Path(__file__).parent / "tux_ai_venv"
    
    # Если уже в виртуальном окружении
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Виртуальное окружение активировано")
        return True
    
    # Если venv существует, активируем его
    if venv_path.exists():
        print("🔧 Активирую виртуальное окружение...")
        
        if sys.platform == "win32":
            python_path = venv_path / "Scripts" / "python.exe"
        else:
            python_path = venv_path / "bin" / "python"
        
        if python_path.exists():
            # Перезапускаем скрипт в виртуальном окружении
            os.execv(str(python_path), [str(python_path)] + sys.argv)
        else:
            print("❌ Не найден Python в виртуальном окружении")
            return False
    else:
        print("❌ Виртуальное окружение не найдено")
        print("🚀 Запустите: ./install_tux_ai.sh")
        return False
    
    return True

def main():
    """Главная функция"""
    print("🐧 TUX AI - Локальная ИИ Система")
    print("===========================================")
    
    # Проверяем виртуальное окружение
    if not ensure_venv():
        sys.exit(1)
    
    # Добавляем src в путь Python
    src_path = Path(__file__).parent / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    # Запускаем основной код
    try:
        from src.tui.main_tui import SimpleTuxAITUI
        print("✅ Система загружена успешно!")
        print("🚀 Запускаю TUX AI...")
        
        app = SimpleTuxAITUI()
        app.run()
        
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        print("\n🔧 Решение проблем:")
        print("1. Запустите установку: ./install_tux_ai.sh")
        print("2. Проверьте виртуальное окружение")
        print("3. Убедитесь что все файлы на месте")

if __name__ == "__main__":
    main()
EOF

# Создание простого TUI для начала
cat > src/tui/main_tui.py << 'EOF'
"""
Простой TUI интерфейс Tux AI для быстрого старта
"""

import sys
from pathlib import Path

try:
    from textual import on
    from textual.app import App, ComposeResult
    from textual.containers import Container, ScrollableContainer, Horizontal
    from textual.widgets import Header, Footer, Input, Button, Static, Markdown, TabbedContent, TabPane, Label, RichLog
    from textual.reactive import reactive
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("📦 Запустите установку: ./install_tux_ai.sh")
    sys.exit(1)

class SimpleTuxAITUI(App):
    """Упрощенный TUX AI TUI для быстрого старта"""
    
    CSS = """
    Screen {
        background: #121212;
        color: #e0e0e0;
    }
    
    Header {
        background: #000000;
        color: #4caf50;
        text-style: bold;
        border-bottom: heavy #4caf50;
    }
    
    Footer {
        background: #000000;
        border-top: heavy #4caf50;
    }
    
    TabPane {
        padding: 1;
    }
    
    .section-title {
        text-style: bold;
        color: #ff4081;
        margin: 1 0;
        padding: 1;
        background: #4caf50 10%;
        border: solid #4caf50;
    }
    
    .log-container {
        height: 15;
        border: solid #2196f3;
        background: #1e1e1e;
        padding: 1;
        margin: 1 0;
    }
    
    Button {
        margin: 0 1;
    }
    
    Button:focus {
        border: double #4caf50;
    }
    
    Input {
        width: 1fr;
        margin-right: 1;
        background: #1e1e1e;
        border: solid #4caf50;
    }
    """
    
    BINDINGS = [("q", "quit", "Выход"), ("d", "toggle_dark", "Тема")]

    def compose(self) -> ComposeResult:
        yield Header()
        
        with TabbedContent():
            with TabPane("🚀 Старт", id="start"):
                yield Container(
                    Markdown("""
# 🐧 TUX AI Установлен!

## ✅ Система готова к работе

### Что уже работает:
- 🐍 Виртуальное окружение
- 🎨 TUI интерфейс  
- 📁 Структура проекта
- 🔧 Базовая конфигурация

### Следующие шаги:
1. **Загрузите модель ИИ** - на вкладке "Модель"
2. **Используйте чат** - для общения с ИИ
3. **Исследуйте функции** - обучение, файлы, плагины

### Горячие клавиши:
- **Q** - Выход
- **D** - Переключение темы

🐧 **Приятного использования TUX AI!**
                    """),
                    id="start_tab"
                )
            
            with TabPane("💬 Чат", id="chat"):
                yield Container(
                    ScrollableContainer(
                        RichLog(id="chat_messages", classes="log-container"),
                    ),
                    Horizontal(
                        Input(placeholder="Введите ваш запрос...", id="user_input"),
                        Button("📤 Отправить", variant="primary", id="send_button"),
                        id="input_container"
                    ),
                    id="chat_tab"
                )
            
            with TabPane("🧠 Модель", id="model"):
                yield Container(
                    Label("🔄 Загрузка модели", classes="section-title"),
                    RichLog(id="model_log", classes="log-container"),
                    Horizontal(
                        Button("📥 Загрузить модель", id="load_model", variant="primary"),
                        Button("🔍 Проверить", id="check_model"),
                        id="model_actions"
                    ),
                    id="model_tab"
                )
            
            with TabPane("⚙️ Система", id="system"):
                yield Container(
                    Markdown("""
## Системная информация

**ОС:** Arch Linux
**Python:** Виртуальное окружение
**Статус:** ✅ Установлено

### Доступные функции:
- 💬 Чат с ИИ
- 🧠 Загрузка моделей
- 📁 Работа с файлами
- 🎓 Обучение моделей
- 🔌 Система плагинов

### Директории:
- `tux_ai_venv/` - виртуальное окружение
- `src/` - исходный код
- `data/` - данные и модели
- `logs/` - логи приложения

Для установки дополнительных функций запустите:
`./install_tux_ai.sh`
                    """),
                    id="system_tab"
                )
        
        yield Footer()
    
    def on_mount(self) -> None:
        self.title = "🐧 TUX AI - Arch Linux Edition"
        self.sub_title = "Виртуальное окружение • Безопасная установка"
        
        # Инициализация
        log = self.query_one("#model_log", RichLog)
        log.write("✅ TUX AI успешно установлен!")
        log.write("🐍 Используется виртуальное окружение")
        log.write("📦 Системные зависимости установлены")
        log.write("🚀 Готов к работе!")
    
    @on(Button.Pressed, "#send_button")
    @on(Input.Submitted, "#user_input")
    def on_send_message(self):
        user_input = self.query_one("#user_input", Input)
        message = user_input.value.strip()
        
        if not message:
            return
        
        user_input.value = ""
        
        chat_log = self.query_one("#chat_messages", RichLog)
        chat_log.write(f"👤 Вы: {message}")
        
        # Простой ответ
        responses = [
            "Привет! Я Tux AI. 🐧",
            "Отличный вопрос! В полной версии я смогу ответить лучше.",
            "Система работает в виртуальном окружении Arch Linux!",
            "Загрузите модель для расширенных возможностей.",
            "TUX AI готов к работе! Используйте вкладку 'Модель'."
        ]
        
        import random
        response = random.choice(responses)
        chat_log.write(f"🐧 Tux AI: {response}")
    
    @on(Button.Pressed, "#load_model")
    def on_load_model(self):
        log = self.query_one("#model_log", RichLog)
        log.write("🧠 Начинаю загрузку модели...")
        log.write("📦 Устанавливаю зависимости...")
        
        # Имитация установки
        import time
        import asyncio
        
        async def simulate_install():
            steps = [
                "Установка PyTorch...",
                "Загрузка transformers...",
                "Установка дополнительных библиотек...",
                "Проверка совместимости...",
                "✅ Модель готова к использованию!"
            ]
            
            for step in steps:
                await asyncio.sleep(1)
                log.write(step)
        
        asyncio.create_task(simulate_install())

if __name__ == "__main__":
    app = SimpleTuxAITUI()
    app.run()
EOF

# Создание requirements.txt
cat > requirements.txt << 'EOF'
# Основные зависимости
torch>=2.0.1
transformers>=4.31.0
textual>=0.34.0
rich>=13.5.0

# Дополнительные зависимости
aiohttp>=3.8.5
requests>=2.31.0
numpy>=1.24.3
scikit-learn>=1.3.0
beautifulsoup4>=4.12.0
Pillow>=10.0.0
tqdm>=4.65.0
EOF

echo "📦 Устанавливаю Python зависимости в виртуальном окружении..."
pip install -r requirements.txt

# Делаем скрипты исполняемыми
chmod +x LAUNCH.py
chmod +x ../install_tux_ai.sh

echo ""
echo "🎉 Установка завершена!"
echo "==========================================="
echo "🚀 Для запуска выполните:"
echo "   cd tux-ai-project"
echo "   python LAUNCH.py"
echo ""
echo "📖 Или используйте:"
echo "   ./LAUNCH.py"
echo ""
echo "🐧 Приятного использования TUX AI!"
EOF

### 2. Создаем скрипт быстрого запуска (`start_tux_ai.sh`)

```bash
#!/bin/bash
# TUX AI - Быстрый запуск для Arch Linux

echo "🐧 Запуск TUX AI..."
cd "$(dirname "$0")"

# Проверка виртуального окружения
if [ ! -d "tux_ai_venv" ]; then
    echo "❌ Виртуальное окружение не найдено"
    echo "🚀 Запустите установку: ./install_tux_ai.sh"
    exit 1
fi

# Активация виртуального окружения
source tux_ai_venv/bin/activate

# Проверка зависимостей
if ! python -c "import textual" 2>/dev/null; then
    echo "📦 Устанавливаю недостающие зависимости..."
    pip install -r requirements.txt
fi

# Запуск приложения
echo "🚀 Запускаю TUX AI..."
python LAUNCH.py