"""
Система плагинов для расширения функциональности Tux AI
"""

import importlib
import inspect
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from abc import ABC, abstractmethod
import json

class TuxPlugin(ABC):
    """Базовый класс для плагинов Tux AI"""
    
    def __init__(self, plugin_manager):
        self.plugin_manager = plugin_manager
        self.name = self.__class__.__name__
        self.version = "1.0.0"
        self.enabled = True
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Возвращает список возможностей плагина"""
        pass
    
    @abstractmethod
    def execute(self, capability: str, **kwargs) -> Any:
        """Выполняет действие плагина"""
        pass
    
    def on_enable(self):
        """Вызывается при включении плагина"""
        pass
    
    def on_disable(self):
        """Вызывается при выключении плагина"""
        pass

class PluginManager:
    """Менеджер плагинов Tux AI"""
    
    def __init__(self, plugins_dir: str = "src/plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.plugins: Dict[str, TuxPlugin] = {}
        self.loaded_plugins: Dict[str, dict] = {}
        self._load_plugin_manifest()
    
    def _load_plugin_manifest(self):
        """Загрузка манифеста плагинов"""
        manifest_path = self.plugins_dir / "manifest.json"
        if manifest_path.exists():
            with open(manifest_path, 'r', encoding='utf-8') as f:
                self.loaded_plugins = json.load(f)
        else:
            self.loaded_plugins = {}
    
    def _save_plugin_manifest(self):
        """Сохранение манифеста плагинов"""
        manifest_path = self.plugins_dir / "manifest.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(self.loaded_plugins, f, indent=2, ensure_ascii=False)
    
    def discover_plugins(self) -> List[str]:
        """Поиск доступных плагинов"""
        plugin_files = self.plugins_dir.glob("*.py")
        plugins = []
        
        for plugin_file in plugin_files:
            if plugin_file.name.startswith("__"):
                continue
            
            plugin_name = plugin_file.stem
            if plugin_name not in self.loaded_plugins:
                self.loaded_plugins[plugin_name] = {
                    "enabled": False,
                    "version": "1.0.0",
                    "capabilities": []
                }
            plugins.append(plugin_name)
        
        self._save_plugin_manifest()
        return plugins
    
    def load_plugin(self, plugin_name: str) -> bool:
        """Загрузка плагина"""
        try:
            if plugin_name in self.plugins:
                return True
            
            # Динамическая загрузка модуля
            spec = importlib.util.spec_from_file_location(
                plugin_name, 
                self.plugins_dir / f"{plugin_name}.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Поиск классов плагинов
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, TuxPlugin) and 
                    obj != TuxPlugin):
                    
                    plugin_instance = obj(self)
                    self.plugins[plugin_name] = plugin_instance
                    
                    # Обновляем манифест
                    self.loaded_plugins[plugin_name] = {
                        "enabled": True,
                        "version": plugin_instance.version,
                        "capabilities": plugin_instance.get_capabilities()
                    }
                    
                    plugin_instance.on_enable()
                    print(f"✅ Плагин загружен: {plugin_name}")
                    return True
            
            return False
            
        except Exception as e:
            print(f"❌ Ошибка загрузки плагина {plugin_name}: {e}")
            return False
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """Выгрузка плагина"""
        if plugin_name in self.plugins:
            self.plugins[plugin_name].on_disable()
            del self.plugins[plugin_name]
            
            self.loaded_plugins[plugin_name]["enabled"] = False
            self._save_plugin_manifest()
            return True
        return False
    
    def execute_plugin(self, plugin_name: str, capability: str, **kwargs) -> Any:
        """Выполнение возможности плагина"""
        if (plugin_name in self.plugins and 
            self.plugins[plugin_name].enabled and
            capability in self.plugins[plugin_name].get_capabilities()):
            
            return self.plugins[plugin_name].execute(capability, **kwargs)
        
        return None
    
    def get_available_capabilities(self) -> Dict[str, List[str]]:
        """Получение списка доступных возможностей"""
        capabilities = {}
        for plugin_name, plugin in self.plugins.items():
            if plugin.enabled:
                capabilities[plugin_name] = plugin.get_capabilities()
        return capabilities
    
    def get_plugin_status(self) -> Dict[str, Dict[str, Any]]:
        """Получение статуса всех плагинов"""
        status = {}
        for plugin_name, plugin in self.plugins.items():
            status[plugin_name] = {
                "enabled": plugin.enabled,
                "version": plugin.version,
                "capabilities": plugin.get_capabilities()
            }
        return status