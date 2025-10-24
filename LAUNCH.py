#!/usr/bin/env python3
"""
🐧 TUX AI - Главный запуск с выбором режима
"""

import os
import sys
import subprocess
from pathlib import Path

def ensure_venv():
    """Проверка виртуального окружения"""
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
    print("=" * 50)
    print("Выберите режим запуска:")
    print("1. 🧠 Нейронная сеть (1000 нейронов)")
    print("2. 💬 Базовый TUI интерфейс") 
    print("3. 🔌 Расширенная версия с плагинами")
    print("4. 🚀 Демонстрация нейронной сети")
    
    choice = input("\nВведите номер (1-4): ").strip()
    
    # Проверяем виртуальное окружение
    if not ensure_venv():
        sys.exit(1)
    
    # Добавляем src в путь Python
    src_path = Path(__file__).parent / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    try:
        if choice == "1":
            from src.tui.neural_tui import NeuralTuxTUI
            print("🚀 Запускаю нейронную сеть Tux AI...")
            app = NeuralTuxTUI()
            app.run()
            
        elif choice == "2":
            from src.tui.main_tui import SimpleTuxAITUI
            print("🚀 Запускаю базовый TUI...")
            app = SimpleTuxAITUI()
            app.run()
            
        elif choice == "3":
            # Здесь можно добавить расширенную версию
            from src.tui.main_tui import SimpleTuxAITUI
            print("🚀 Запускаю TUX AI...")
            app = SimpleTuxAITUI()
            app.run()
            
        elif choice == "4":
            from src.core.tux_neural_network import demonstrate_tux_ai
            demonstrate_tux_ai()
            
        else:
            print("❌ Неверный выбор. Запускаю базовую версию...")
            from src.tui.main_tui import SimpleTuxAITUI
            app = SimpleTuxAITUI()
            app.run()
            
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        print("\n🔧 Решение проблем:")
        print("1. Запустите установку: ./install_tux_ai.sh")
        print("2. Установите PyTorch: pip install torch")
        print("3. Проверьте структуру проекта")

if __name__ == "__main__":
    main()