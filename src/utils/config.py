"""
Конфигурация TUX AI для Arch Linux
"""

from pathlib import Path
import os

class TuxConfig:
    """Конфигурация TUX AI"""
    
    # Пути
    BASE_DIR = Path(__file__).parent.parent.parent
    VENV_DIR = BASE_DIR / "tux_ai_venv"
    DATA_DIR = BASE_DIR / "data"
    LOGS_DIR = BASE_DIR / "logs"
    
    # Настройки модели
    MODEL_NAME = "sberbank-ai/rugpt3small_based_on_gpt2"
    MODEL_CACHE = DATA_DIR / "models"
    
    # Настройки TUI
    TUI_THEME = "dark"
    TUI_LANGUAGE = "ru"
    
    @classmethod
    def setup_directories(cls):
        """Создание необходимых директорий"""
        directories = [
            cls.DATA_DIR / "models",
            cls.DATA_DIR / "uploads", 
            cls.DATA_DIR / "training",
            cls.DATA_DIR / "memory",
            cls.LOGS_DIR
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def check_environment(cls):
        """Проверка окружения"""
        checks = {
            "Виртуальное окружение": cls.VENV_DIR.exists(),
            "Директория данных": cls.DATA_DIR.exists(),
            "Директория логов": cls.LOGS_DIR.exists(),
        }
        
        status = {}
        for name, check in checks.items():
            status[name] = "✅" if check else "❌"
        
        return status