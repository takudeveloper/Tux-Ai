#!/usr/bin/env python3
"""
Установщик Tux AI для Arch Linux
Решает проблему externally-managed-environment
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, check=True):
    """Выполнить команду в shell"""
    print(f"🚀 Выполняю: {command}")
    try:
        result = subprocess.run(command, shell=True, check=check, 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Успех")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка: {e}")
        return None

def install_system_dependencies():
    """Установка системных зависимостей для Arch Linux"""
    print("🐧 Устанавливаю системные зависимости для Arch Linux...")
    
    commands = [
        "sudo pacman -S --noconfirm python-pip",
        "sudo pacman -S --noconfirm tesseract",
        "sudo pacman -S --noconfirm tesseract-data-rus",
        "sudo pacman -S --noconfirm poppler",
        "sudo pacman -S --noconfirm python-virtualenv"
    ]
    
    for cmd in commands:
        if run_command(cmd) is None:
            print(f"⚠️  Пропускаю: {cmd}")

def create_project_structure():
    """Создание структуры проекта"""
    print("📁 Создаю структуру проекта...")
    
    directories = [
        "src/tui",
        "data/models", 
        "data/uploads",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"📁 Создана: {directory}")
    
    # Создаем __init__.py файлы
    init_files = ["src/__init__.py", "src/tui/__init__.py"]
    for init_file in init_files:
        with open(init_file, 'w') as f:
            f.write('"""Package initialization"""\n')
        print(f"📄 Создан: {init_file}")

def setup_virtual_environment():
    """Настройка виртуального окружения"""
    print("🐍 Настраиваю виртуальное окружение...")
    
    venv_path = Path("venv")
    if venv_path.exists():
        print("✅ Виртуальное окружение уже существует")
        return True
    
    # Создаем виртуальное окружение
    result = run_command(f"{sys.executable} -m venv venv")
    if result is None or result.returncode != 0:
        print("❌ Не удалось создать виртуальное окружение")
        return False
    
    # Определяем путь к pip в venv
    if sys.platform == "win32":
        pip_path = venv_path / "Scripts" / "pip.exe"
    else:
        pip_path = venv_path / "bin" / "pip"
    
    if not pip_path.exists():
        print("❌ Виртуальное окружение создано неправильно")
        return False
    
    print("✅ Виртуальное окружение создано")
    return str(pip_path)

def install_python_dependencies(pip_path):
    """Установка Python зависимостей"""
    print("📦 Устанавливаю Python зависимости...")
    
    # Устанавливаем pip в виртуальном окружении
    run_command(f"{pip_path} install --upgrade pip")
    
    # Устанавливаем зависимости
    if Path("requirements.txt").exists():
        result = run_command(f"{pip_path} install -r requirements.txt")
    else:
        # Устанавливаем основные зависимости
        deps = [
            "torch", 
            "transformers",
            "textual",
            "rich", 
            "fastapi",
            "uvicorn",
            "aiohttp",
            "requests"
        ]
        for dep in deps:
            print(f"📥 Устанавливаю {dep}...")
            run_command(f"{pip_path} install {dep}")
    
    print("✅ Зависимости установлены")

def main():
    """Главная функция установки"""
    print("🐧 Установка Tux AI для Arch Linux")
    print("=" * 50)
    
    # Системные зависимости
    install_system_dependencies()
    
    # Структура проекта
    create_project_structure()
    
    # Виртуальное окружение
    pip_path = setup_virtual_environment()
    if not pip_path:
        print("❌ Не удалось настроить виртуальное окружение")
        return
    
    # Python зависимости
    install_python_dependencies(pip_path)
    
    print("\n🎉 Установка завершена успешно!")
    print("\n🚀 Запустите проект:")
    print("   python LAUNCH.py")
    print("\n📖 Или используйте скрипт:")
    print("   chmod +x start_linux.sh && ./start_linux.sh")

if __name__ == "__main__":
    main()