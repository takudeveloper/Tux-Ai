"""
Главный TUI интерфейс Tux AI с поддержкой плагинов и памяти
"""

import sys
import asyncio
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from textual import on, work
    from textual.app import App, ComposeResult
    from textual.containers import Container, ScrollableContainer, Horizontal, Vertical, Grid
    from textual.widgets import (
        Header, Footer, Input, Button, Static, Markdown, 
        TabbedContent, TabPane, Label, ListView, ListItem, 
        LoadingIndicator, ProgressBar, RichLog, DataTable, SelectionList,
        Switch, Select, TextArea
    )
    from textual.reactive import reactive
    from textual.binding import Binding
    
    from src.core.model_engine import TuxModelEngine, SimpleFallbackModel
    from src.core.training_system import TrainingSystem
    from src.core.file_manager import FileManager
    from src.core.memory_system import MemorySystem
    from src.core.plugin_system import PluginManager
    
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("📦 Установите зависимости: pip install textual rich transformers torch scikit-learn")
    sys.exit(1)

class PluginStatus(Static):
    """Статус плагинов"""
    
    def render(self) -> str:
        app = self.app
        if hasattr(app, 'plugin_manager'):
            enabled_plugins = sum(1 for p in app.plugin_manager.plugins.values() if p.enabled)
            return f"🔌 Плагины: {enabled_plugins}/{len(app.plugin_manager.plugins)} активны"
        return "🔌 Плагины: не загружены"

class MemoryStatus(Static):
    """Статус памяти"""
    
    def render(self) -> str:
        app = self.app
        if hasattr(app, 'memory_system'):
            return "🧠 Память: активна"
        return "🧠 Память: неактивна"

class AdvancedTuxAITUI(App):
    """
    🐧 Продвинутый TUX AI TUI
    С плагинами, памятью и расширенными возможностями
    """
    
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
        padding: 0 1;
    }
    
    Footer {
        background: #000000;
        border-top: heavy #4caf50;
        padding: 0 1;
    }
    
    TabbedContent {
        height: 100%;
    }
    
    TabPane {
        padding: 1;
    }
    
    .section-title {
        text-style: bold;
        color: #ff4081;
        margin-bottom: 1;
        background: #4caf50 10%;
        padding: 1;
        border: solid #4caf50;
    }
    
    .status-panel {
        layout: horizontal;
        height: auto;
        margin: 1 0;
    }
    
    .status-widget {
        background: #2d2d2d;
        padding: 1;
        margin: 0 1;
        border: solid #ff9800;
        width: 1fr;
    }
    
    .log-container {
        height: 10;
        border: solid #2196f3;
        background: #1e1e1e;
        padding: 1;
        margin: 1 0;
    }
    
    .chat-container {
        height: 20;
        border: solid #4caf50;
        background: #1e1e1e;
        padding: 1;
        margin: 1 0;
    }
    
    .plugin-container {
        border: solid #9c27b0;
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
    
    Button#send_button {
        background: #4caf50;
        color: white;
    }
    
    Button#train_button {
        background: #ff9800;
        color: black;
    }
    
    Button#load_model {
        background: #2196f3;
        color: white;
    }
    
    Button#plugin_button {
        background: #9c27b0;
        color: white;
    }
    
    Input {
        width: 1fr;
        margin-right: 1;
        background: #1e1e1e;
        border: solid #4caf50;
    }
    
    ProgressBar {
        height: 1;
        margin: 1 0;
    }
    
    ProgressBar .progress-bar--bar {
        background: #4caf50;
    }
    
    ListView {
        height: 12;
        border: solid #2196f3;
        background: #1e1e1e;
        margin: 1 0;
    }
    
    ListItem {
        padding: 1;
    }
    
    ListItem:hover {
        background: #4caf50 20%;
    }
    
    Switch:checked {
        background: #4caf50;
    }
    
    Grid {
        grid-size: 2;
        grid-gutter: 1;
    }
    """
    
    BINDINGS = [
        ("q", "quit", "Выход"),
        ("d", "toggle_dark", "Тема"),
        ("f", "focus_files", "Файлы"),
        ("t", "focus_training", "Обучение"),
        ("c", "focus_chat", "Чат"),
        ("p", "focus_plugins", "Плагины"),
        ("r", "refresh_all", "Обновить"),
        ("l", "load_model", "Загрузить модель"),
    ]
    
    # Reactive переменные
    model_loaded = reactive(False)
    training_in_progress = reactive(False)
    plugins_loaded = reactive(False)
    
    def __init__(self):
        super().__init__()
        # Инициализация систем
        self.model_engine = TuxModelEngine()
        self.fallback_model = SimpleFallbackModel()
        self.file_manager = FileManager()
        self.training_system = TrainingSystem(self.model_engine)
        self.memory_system = MemorySystem()
        self.plugin_manager = PluginManager()
        
        self.current_model = self.fallback_model
        self.chat_history = []
        self.current_session_id = f"session_{int(asyncio.get_event_loop().time())}"
    
    def compose(self) -> ComposeResult:
        """Создание интерфейса"""
        yield Header()
        
        # Панель статуса
        yield Container(
            Horizontal(
                PluginStatus(classes="status-widget"),
                MemoryStatus(classes="status-widget"),
                id="status_panel"
            )
        )
        
        with TabbedContent(initial="chat"):
            # Вкладка чата
            with TabPane("💬 Чат", id="chat"):
                yield Container(
                    ScrollableContainer(
                        RichLog(id="chat_messages", classes="chat-container"),
                    ),
                    Horizontal(
                        Input(
                            placeholder="Введите ваш запрос...", 
                            id="user_input"
                        ),
                        Button("📤 Отправить", variant="primary", id="send_button"),
                        Button("🧠 Исп. память", id="use_memory"),
                        id="input_container"
                    ),
                    id="chat_tab"
                )
            
            # Вкладка файлов
            with TabPane("📁 Файлы", id="files"):
                yield Container(
                    Label("📁 Загрузка файлов", classes="section-title"),
                    Horizontal(
                        Button("📎 Загрузить демо", id="upload_demo", variant="primary"),
                        Button("🔄 Обновить", id="refresh_files"),
                        Button("🗑️ Очистить", id="clear_files", variant="error"),
                        id="file_actions"
                    ),
                    RichLog(id="upload_log", classes="log-container"),
                    Label("📋 Загруженные файлы", classes="section-title"),
                    ListView(id="file_list"),
                    Horizontal(
                        Button("🎓 Обучиться на файлах", id="train_on_files", variant="success"),
                        Button("👁️ Просмотреть", id="view_file"),
                        id="file_training_actions"
                    ),
                    id="files_tab"
                )
            
            # Вкладка обучения
            with TabPane("🎓 Обучение", id="training"):
                yield Container(
                    Label("🌐 Обучение на интернет-данных", classes="section-title"),
                    Input(placeholder="Тема для обучения...", id="training_query"),
                    Horizontal(
                        Button("🔍 Найти и обучить", variant="success", id="train_internet"),
                        Button("🔄 История обучения", id="training_history"),
                        id="internet_training"
                    ),
                    
                    Label("⚙️ Управление моделью", classes="section-title"),
                    Horizontal(
                        Button("🧠 Загрузить модель", id="load_model", variant="primary"),
                        Button("💾 Сохранить модель", id="save_model"),
                        id="model_actions"
                    ),
                    
                    ProgressBar(total=100, show_eta=False, id="training_progress"),
                    RichLog(id="training_log", classes="log-container"),
                    id="training_tab"
                )
            
            # Вкладка плагинов
            with TabPane("🔌 Плагины", id="plugins"):
                yield Container(
                    Label("🔌 Управление плагинами", classes="section-title"),
                    Horizontal(
                        Button("🔍 Обнаружить", id="discover_plugins", variant="primary"),
                        Button("🔄 Загрузить все", id="load_all_plugins"),
                        Button("📋 Статус", id="plugins_status"),
                        id="plugin_actions"
                    ),
                    RichLog(id="plugins_log", classes="log-container"),
                    Label("📋 Доступные плагины", classes="section-title"),
                    ListView(id="plugins_list"),
                    Horizontal(
                        Button("▶️ Включить", id="enable_plugin", variant="success"),
                        Button("⏹️ Выключить", id="disable_plugin"),
                        Button("⚙️ Выполнить", id="execute_plugin", variant="warning"),
                        id="plugin_controls"
                    ),
                    id="plugins_tab"
                )
            
            # Вкладка памяти
            with TabPane("🧠 Память", id="memory"):
                yield Container(
                    Label("🧠 Система памяти", classes="section-title"),
                    Horizontal(
                        Button("📊 Статистика", id="memory_stats"),
                        Button("🔍 Поиск", id="memory_search"),
                        Button("🧹 Очистка", id="memory_cleanup", variant="error"),
                        id="memory_actions"
                    ),
                    Input(placeholder="Поиск в памяти...", id="memory_query"),
                    RichLog(id="memory_log", classes="log-container"),
                    DataTable(id="memory_table"),
                    id="memory_tab"
                )
            
            # Вкладка системы
            with TabPane("ℹ️ Система", id="system"):
                yield Container(
                    Markdown("""
# 🐧 TUX AI System

## Статус системы:
- **Модель ИИ:** {"Загружена" if self.model_loaded else "Демо-режим"}
- **Плагины:** {"Загружены" if self.plugins_loaded else "Не загружены"}
- **Память:** Активна
- **Файлов загружено:** 0
- **Сессий обучения:** 0

## Новые возможности:
- 🔌 **Система плагинов** - расширяемая архитектура
- 🧠 **Долговременная память** - запоминание контекста
- 🔍 **Веб-поиск** - доступ к актуальной информации
- 💻 **Анализ кода** - интеллектуальная работа с кодом
- 📊 **Профили пользователей** - персонализация

## Горячие клавиши:
- **Q** - Выход
- **D** - Переключение темы  
- **F** - Файлы
- **T** - Обучение
- **C** - Чат
- **P** - Плагины
- **R** - Обновить
- **L** - Загрузить модель

## Следующие шаги:
1. Загрузите модель для полной функциональности
2. Активируйте плагины для расширения возможностей
3. Используйте память для сохранения контекста
4. Обучите модель на своих данных
                    """),
                    id="system_tab"
                )
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Инициализация при запуске"""
        self.title = "🐧 TUX AI - Расширенная Локальная ИИ Система"
        self.sub_title = "Плагины • Память • Обучение"
        
        # Инициализация системы
        self._initialize_system()
    
    def _initialize_system(self):
        """Инициализация системных компонентов"""
        log = self.query_one("#upload_log", RichLog)
        log.write("🚀 Инициализация TUX AI...")
        log.write("✅ TUI интерфейс загружен")
        log.write("📁 Файловая система готова")
        log.write("🎓 Система обучения инициализирована")
        
        # Загрузка плагинов
        self._load_plugins()
        
        # Обновляем списки
        self._update_file_list()
        self._update_plugins_list()
        
        log.write("🐧 Система инициализирована успешно!")
    
    def _load_plugins(self):
        """Загрузка плагинов"""
        plugins_log = self.query_one("#plugins_log", RichLog)
        plugins_log.write("🔌 Загружаю плагины...")
        
        # Обнаруживаем плагины
        discovered = self.plugin_manager.discover_plugins()
        plugins_log.write(f"📋 Найдено плагинов: {len(discovered)}")
        
        # Загружаем основные плагины
        core_plugins = ['web_search', 'code_analyzer']
        loaded_count = 0
        
        for plugin_name in core_plugins:
            if plugin_name in discovered:
                if self.plugin_manager.load_plugin(plugin_name):
                    loaded_count += 1
                    plugins_log.write(f"✅ Загружен: {plugin_name}")
                else:
                    plugins_log.write(f"❌ Ошибка загрузки: {plugin_name}")
        
        self.plugins_loaded = loaded_count > 0
        plugins_log.write(f"🎯 Загружено плагинов: {loaded_count}/{len(core_plugins)}")
    
    def _update_file_list(self):
        """Обновление списка файлов"""
        file_list = self.query_one("#file_list", ListView)
        file_list.clear()
        
        files = self.file_manager.list_files()
        for file_info in files:
            status = "✅" if file_info['used_in_training'] else "📄"
            file_item = ListItem(
                Label(f"{status} {file_info['name']} ({file_info['size']} bytes)"),
                id=f"file_{file_info['id']}"
            )
            file_list.append(file_item)
    
    def _update_plugins_list(self):
        """Обновление списка плагинов"""
        plugins_list = self.query_one("#plugins_list", ListView)
        plugins_list.clear()
        
        for plugin_name, plugin in self.plugin_manager.plugins.items():
            status = "🟢" if plugin.enabled else "🔴"
            plugin_item = ListItem(
                Label(f"{status} {plugin_name} v{plugin.version}"),
                id=f"plugin_{plugin_name}"
            )
            plugins_list.append(plugin_item)
    
    @on(Button.Pressed, "#send_button")
    @on(Input.Submitted, "#user_input")
    def on_send_message(self):
        """Обработка отправки сообщения"""
        user_input = self.query_one("#user_input", Input)
        message = user_input.value.strip()
        
        if not message:
            return
        
        user_input.value = ""
        
        # Добавляем сообщение пользователя
        chat_log = self.query_one("#chat_messages", RichLog)
        chat_log.write(f"👤 [bold cyan]Вы:[/bold cyan] {message}")
        
        # Генерируем ответ
        self._generate_ai_response(message)
    
    @work
    async def _generate_ai_response(self, prompt: str):
        """Генерация ответа ИИ с использованием памяти"""
        chat_log = self.query_one("#chat_messages", RichLog)
        
        # Показываем индикатор thinking
        thinking_id = f"thinking_{len(self.chat_history)}"
        chat_log.write(f"🐧 [bold green]Tux AI:[/bold green] [italic]думает...[/italic]", id=thinking_id)
        
        try:
            # Получаем релевантный контекст из памяти
            context = ""
            relevant_memories = self.memory_system.get_relevant_context(prompt, limit=3)
            
            if relevant_memories:
                context = "\nРелевантный контекст из предыдущих разговоров:\n"
                for memory in relevant_memories:
                    context += f"- Пользователь: {memory['user_message']}\n"
                    context += f"- Tux AI: {memory['ai_response']}\n\n"
            
            # Добавляем контекст к промпту
            enhanced_prompt = f"{context}Текущий вопрос: {prompt}"
            
            # Генерируем ответ (в фоновом потоке)
            response = await asyncio.to_thread(
                self.current_model.generate_response, 
                enhanced_prompt,
                max_length=200,
                temperature=0.7
            )
            
            # Сохраняем в память
            self.memory_system.save_conversation(
                self.current_session_id,
                prompt,
                response,
                importance=1
            )
            
            # Обновляем чат
            chat_log.remove(thinking_id)
            chat_log.write(f"🐧 [bold green]Tux AI:[/bold green] {response}")
            
            # Сохраняем в историю
            self.chat_history.append({
                "user": prompt,
                "ai": response,
                "timestamp": asyncio.get_event_loop().time()
            })
            
        except Exception as e:
            chat_log.remove(thinking_id)
            chat_log.write(f"❌ [bold red]Ошибка:[/bold red] {str(e)}")
    
    @on(Button.Pressed, "#use_memory")
    def on_use_memory(self):
        """Использование памяти для улучшения ответа"""
        chat_log = self.query_one("#chat_messages", RichLog)
        user_input = self.query_one("#user_input", Input)
        prompt = user_input.value.strip()
        
        if not prompt:
            self.notify("⚠️ Введите запрос для поиска в памяти")
            return
        
        # Ищем в памяти
        memories = self.memory_system.get_relevant_context(prompt, limit=5)
        
        if memories:
            chat_log.write("🧠 Найдено в памяти:")
            for i, memory in enumerate(memories, 1):
                chat_log.write(f"{i}. Q: {memory['user_message'][:50]}...")
                chat_log.write(f"   A: {memory['ai_response'][:50]}...")
        else:
            chat_log.write("🧠 В памяти не найдено релевантной информации")
    
    @on(Button.Pressed, "#discover_plugins")
    def on_discover_plugins(self):
        """Обнаружение плагинов"""
        plugins_log = self.query_one("#plugins_log", RichLog)
        discovered = self.plugin_manager.discover_plugins()
        plugins_log.write(f"🔍 Обнаружено плагинов: {len(discovered)}")
        for plugin in discovered:
            plugins_log.write(f"📦 {plugin}")
        
        self._update_plugins_list()
    
    @on(Button.Pressed, "#load_all_plugins")
    def on_load_all_plugins(self):
        """Загрузка всех плагинов"""
        plugins_log = self.query_one("#plugins_log", RichLog)
        discovered = self.plugin_manager.discover_plugins()
        loaded_count = 0
        
        for plugin_name in discovered:
            if plugin_name not in self.plugin_manager.plugins:
                if self.plugin_manager.load_plugin(plugin_name):
                    loaded_count += 1
                    plugins_log.write(f"✅ Загружен: {plugin_name}")
                else:
                    plugins_log.write(f"❌ Ошибка загрузки: {plugin_name}")
        
        plugins_log.write(f"🎯 Итого загружено: {loaded_count}")
        self._update_plugins_list()
        self.plugins_loaded = loaded_count > 0
    
    @on(Button.Pressed, "#enable_plugin")
    def on_enable_plugin(self):
        """Включение выбранного плагина"""
        plugins_list = self.query_one("#plugins_list", ListView)
        if plugins_list.index is not None:
            selected_item = plugins_list.children[plugins_list.index]
            plugin_name = selected_item.id.replace("plugin_", "")
            
            if plugin_name in self.plugin_manager.plugins:
                self.plugin_manager.plugins[plugin_name].enabled = True
                self.plugin_manager.plugins[plugin_name].on_enable()
                self._update_plugins_list()
                self.notify(f"✅ Плагин {plugin_name} включен")
    
    @on(Button.Pressed, "#execute_plugin")
    @work
    async def on_execute_plugin(self):
        """Выполнение выбранного плагина"""
        plugins_list = self.query_one("#plugins_list", ListView)
        plugins_log = self.query_one("#plugins_log", RichLog)
        
        if plugins_list.index is not None:
            selected_item = plugins_list.children[plugins_list.index]
            plugin_name = selected_item.id.replace("plugin_", "")
            
            if (plugin_name in self.plugin_manager.plugins and 
                self.plugin_manager.plugins[plugin_name].enabled):
                
                plugin = self.plugin_manager.plugins[plugin_name]
                capabilities = plugin.get_capabilities()
                
                plugins_log.write(f"⚙️ Выполняю плагин: {plugin_name}")
                plugins_log.write(f"📋 Возможности: {', '.join(capabilities)}")
                
                # Для веб-поиска выполняем демо-поиск
                if plugin_name == "WebSearch" and "web_search" in capabilities:
                    try:
                        result = await plugin.execute("web_search", query="Tux AI искусственный интеллект")
                        plugins_log.write("🔍 Результаты поиска:")
                        for i, item in enumerate(result[:3], 1):
                            plugins_log.write(f"{i}. {item.get('title', 'Без названия')}")
                    except Exception as e:
                        plugins_log.write(f"❌ Ошибка: {e}")
                
                # Для анализа кода
                elif plugin_name == "CodeAnalyzer" and "analyze_python_code" in capabilities:
                    demo_code = """
def calculate_sum(a, b):
    return a + b

class MathOperations:
    def multiply(self, x, y):
        return x * y
"""
                    result = plugin.execute("analyze_python_code", code=demo_code)
                    if result and result.get('valid'):
                        plugins_log.write(f"✅ Анализ кода: {result['functions']} функций, {result['classes']} классов")
    
    @on(Button.Pressed, "#memory_stats")
    def on_memory_stats(self):
        """Статистика памяти"""
        memory_log = self.query_one("#memory_log", RichLog)
        profile = self.memory_system.get_user_profile()
        
        memory_log.write("📊 Статистика памяти:")
        memory_log.write(f"💬 Разговоров: {profile['statistics']['total_conversations']}")
        memory_log.write(f"📚 Тем: {profile['statistics']['unique_topics']}")
        memory_log.write(f"⏰ Последняя активность: {profile['statistics']['last_active']}")
        
        # Показываем предпочтения
        if profile['preferences']:
            memory_log.write("🎯 Предпочтения пользователя:")
            for pref_type, pref_data in profile['preferences'].items():
                memory_log.write(f"  - {pref_type}: {pref_data['value']} (сила: {pref_data['strength']:.2f})")
    
    @on(Button.Pressed, "#memory_search")
    @on(Input.Submitted, "#memory_query")
    def on_memory_search(self):
        """Поиск в памяти"""
        memory_query = self.query_one("#memory_query", Input)
        query = memory_query.value.strip()
        memory_log = self.query_one("#memory_log", RichLog)
        memory_table = self.query_one("#memory_table", DataTable)
        
        if not query:
            self.notify("⚠️ Введите запрос для поиска")
            return
        
        memories = self.memory_system.get_relevant_context(query, limit=10)
        memory_log.write(f"🔍 Найдено результатов: {len(memories)}")
        
        # Очищаем и настраиваем таблицу
        memory_table.clear(columns=True)
        memory_table.add_columns("Сходство", "Вопрос", "Ответ", "Тема")
        
        for memory in memories:
            memory_table.add_row(
                f"{memory['similarity']:.3f}",
                memory['user_message'][:50] + "...",
                memory['ai_response'][:50] + "...", 
                memory['topic'] or "Без темы"
            )
    
    # ... остальные методы (on_upload_demo_file, on_load_model, on_train_internet, etc.)
    # остаются аналогичными предыдущей версии, но с небольшими улучшениями
    
    def action_focus_plugins(self):
        """Переключение на вкладку плагинов"""
        self.query_one(TabbedContent).active = "plugins"
        self.notify("🔌 Переключено на плагины")
    
    def action_refresh_all(self):
        """Обновление всех данных"""
        self.notify("🔄 Обновляю систему...")
        self._initialize_system()

def main():
    """Запуск приложения"""
    try:
        app = AdvancedTuxAITUI()
        app.run()
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        print("🔧 Решение проблем:")
        print("1. Запустите: python setup_environment.py")
        print("2. Убедитесь что установлены все зависимости")
        print("3. Проверьте доступное место на диске")

if __name__ == "__main__":
    main()