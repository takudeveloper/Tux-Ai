"""
TUI интерфейс для управления нейронной сетью Tux AI
"""

import sys
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
        LoadingIndicator, ProgressBar, RichLog, DataTable, SelectionList
    )
    from textual.reactive import reactive
    from textual.binding import Binding
    
    from src.core.tux_neural_network import TuxAICore, demonstrate_tux_ai
    
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)

class NeuronVisualization(Static):
    """Визуализация активности нейронов"""
    
    def render(self) -> str:
        app = self.app
        if hasattr(app, 'tux_core'):
            stats = app.tux_core.main_network.get_neuron_statistics()
            if "error" not in stats:
                active = stats["active_neurons"]
                total = stats["total_neurons"]
                distribution = stats["activation_distribution"]
                
                return f"""
🧠 Активность нейронов: {active}/{total}

📊 Распределение активаций:
  🔴 Очень низкая: {distribution['very_low']}
  🟡 Низкая: {distribution['low']}  
  🟢 Средняя: {distribution['medium']}
  🔵 Высокая: {distribution['high']}

📈 Средняя активация: {stats['avg_activation']:.3f}
                """
        return "🧠 Нейронная сеть не инициализирована"

class TrainingProgress(Static):
    """Прогресс обучения"""
    
    progress = reactive(0)
    status = reactive("Готов к обучению")
    
    def render(self) -> str:
        if self.progress == 0:
            return f"🎓 {self.status}"
        else:
            return f"🎓 {self.status} [{self.progress}%]"

class NeuralTuxTUI(App):
    """
    TUI для нейронной сети Tux AI
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
    
    .neuron-viz {
        background: #2d2d2d;
        padding: 1;
        margin: 1 0;
        border: solid #9c27b0;
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
    
    Button {
        margin: 0 1;
    }
    
    Button:focus {
        border: double #4caf50;
    }
    
    Button#train_button {
        background: #ff9800;
        color: black;
    }
    
    Button#analyze_image {
        background: #9c27b0;
        color: white;
    }
    
    Button#analyze_text {
        background: #2196f3;
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
    
    Grid {
        grid-size: 2;
        grid-gutter: 1;
    }
    """
    
    BINDINGS = [
        ("q", "quit", "Выход"),
        ("d", "toggle_dark", "Тема"),
        ("n", "focus_neurons", "Нейроны"),
        ("t", "focus_training", "Обучение"),
        ("a", "focus_analysis", "Анализ"),
        ("r", "refresh_stats", "Обновить"),
    ]
    
    def __init__(self):
        super().__init__()
        self.tux_core = TuxAICore()
        self.training_in_progress = False
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        with TabbedContent(initial="neurons"):
            # Вкладка нейронов
            with TabPane("🧠 Нейроны", id="neurons"):
                yield Container(
                    NeuronVisualization(classes="neuron-viz"),
                    Label("📊 Статистика сети", classes="section-title"),
                    Grid(
                        Container(
                            Label("Основная сеть"),
                            RichLog(id="main_network_log", classes="log-container"),
                        ),
                        Container(
                            Label("Визуальная сеть"),
                            RichLog(id="vision_network_log", classes="log-container"),
                        ),
                    ),
                    Horizontal(
                        Button("🔄 Обновить статистику", id="refresh_stats"),
                        Button("💾 Сохранить модель", id="save_model"),
                        Button("📥 Загрузить модель", id="load_model"),
                        id="neuron_actions"
                    ),
                    id="neurons_tab"
                )
            
            # Вкладка обучения
            with TabPane("🎓 Обучение", id="training"):
                yield Container(
                    Label("🎓 Обучение нейронной сети", classes="section-title"),
                    Horizontal(
                        Button("🖼️ Обучить на изображениях", id="train_images", variant="warning"),
                        Button("📚 Обучить на текстах", id="train_texts"),
                        Button("🔄 Демо-обучение", id="demo_train", variant="success"),
                        id="training_buttons"
                    ),
                    TrainingProgress(classes="status-widget"),
                    ProgressBar(total=100, show_eta=False, id="training_progress"),
                    RichLog(id="training_log", classes="log-container"),
                    id="training_tab"
                )
            
            # Вкладка анализа
            with TabPane("🔍 Анализ", id="analysis"):
                yield Container(
                    Label("🖼️ Анализ изображений", classes="section-title"),
                    Horizontal(
                        Button("📁 Анализ изображения", id="analyze_image", variant="primary"),
                        Button("🔄 Демо-анализ", id="demo_analyze"),
                        id="image_analysis"
                    ),
                    RichLog(id="image_log", classes="log-container"),
                    
                    Label("💬 Анализ текста", classes="section-title"),
                    Horizontal(
                        Input(placeholder="Введите текст для анализа...", id="text_input"),
                        Button("📊 Анализировать", id="analyze_text"),
                        id="text_analysis"
                    ),
                    RichLog(id="text_log", classes="log-container"),
                    id="analysis_tab"
                )
            
            # Вкладка информации
            with TabPane("ℹ️ О сети", id="info"):
                yield Container(
                    Markdown("""
# 🧠 Tux AI Neural Network

## Архитектура сети:
- **1000 точно нейронов** в скрытых слоях
- **5 полносвязных слоев**: 400 -> 300 -> 200 -> 100 -> выход
- **Функция активации**: ReLU
- **Dropout**: 0.2 для регуляризации

## Возможности:
- 🖼️ **Анализ изображений** через сверточную сеть
- 💬 **Обработка текста** через основную сеть  
- 🎓 **Обучение** на пользовательских данных
- 📊 **Визуализация** активности нейронов

## Технические детали:
- **Входной размер**: 784 (28x28 изображения или текст)
- **Выходной размер**: настраиваемый (по умолчанию 10)
- **Параметры**: ~500,000 обучаемых параметров
- **Реализация**: Pure PyTorch

## Горячие клавиши:
- **Q** - Выход
- **D** - Переключение темы
- **N** - Нейроны
- **T** - Обучение  
- **A** - Анализ
- **R** - Обновить статистику

## Следующие шаги:
1. Запустите демо-обучение для тестирования
2. Проанализируйте текст или изображения
3. Изучите статистику нейронов
4. Сохраните обученную модель
                    """),
                    id="info_tab"
                )
        
        yield Footer()
    
    def on_mount(self) -> None:
        self.title = "🧠 Tux AI Neural Network - 1000 Нейронов"
        self.sub_title = "Анализ изображений • Обработка текста • Обучение"
        
        # Инициализация
        self._initialize_networks()
    
    def _initialize_networks(self):
        """Инициализация нейронных сетей"""
        log = self.query_one("#main_network_log", RichLog)
        log.write("🧠 Инициализация нейронных сетей...")
        
        # Информация о сетях
        info = self.tux_core.get_network_info()
        
        log.write("✅ Основная сеть инициализирована")
        log.write(f"📊 Нейронов: {info['main_network']['total_neurons']}")
        log.write(f"🔧 Параметров: {info['main_network']['parameters']}")
        
        vision_log = self.query_one("#vision_network_log", RichLog)
        vision_log.write("✅ Визуальная сеть инициализирована")
        vision_log.write(f"📊 Сверточных слоев: {info['vision_network']['conv_layers']}")
        vision_log.write(f"🔧 Параметров: {info['vision_network']['parameters']}")
    
    @on(Button.Pressed, "#refresh_stats")
    def on_refresh_stats(self):
        """Обновление статистики"""
        self._initialize_networks()
        self.notify("🔄 Статистика обновлена")
    
    @on(Button.Pressed, "#demo_train")
    def on_demo_train(self):
        """Демонстрационное обучение"""
        if self.training_in_progress:
            self.notify("⚠️ Обучение уже идет...")
            return
        
        self.training_in_progress = True
        progress = self.query_one("#training_progress", ProgressBar)
        status = self.query_one(TrainingProgress)
        log = self.query_one("#training_log", RichLog)
        
        status.status = "Демо-обучение..."
        progress.update(progress=25)
        log.write("🎓 Начинаю демонстрационное обучение...")
        
        @work
        async def training_task():
            try:
                # Имитация прогресса обучения
                for i in range(5):
                    await asyncio.sleep(1)
                    progress.advance(15)
                    log.write(f"📚 Эпоха {i+1}/5: обучение...")
                
                # Запуск реального демо-обучения
                result = await asyncio.to_thread(
                    self.tux_core.train_on_images, "demo", 3
                )
                
                if result["success"]:
                    status.status = "Обучение завершено!"
                    progress.update(progress=100)
                    log.write("✅ Демо-обучение завершено!")
                    log.write(f"📊 Циклов обучения: {result['training_cycles']}")
                    log.write(f"📉 Финальные потери: {result['final_loss']:.4f}")
                    
                    # Обновление статистики нейронов
                    self._initialize_networks()
                    
                    self.notify("🎓 Демо-обучение завершено!")
                else:
                    status.status = "Ошибка обучения"
                    progress.update(progress=0)
                    log.write(f"❌ Ошибка: {result.get('error', 'Неизвестная ошибка')}")
                    self.notify("❌ Ошибка обучения")
                
            except Exception as e:
                status.status = "Ошибка"
                progress.update(progress=0)
                log.write(f"❌ Исключение: {str(e)}")
                self.notify(f"❌ Ошибка: {str(e)}")
            
            finally:
                self.training_in_progress = False
        
        training_task()
    
    @on(Button.Pressed, "#analyze_text")
    @on(Input.Submitted, "#text_input")
    def on_analyze_text(self):
        """Анализ текста"""
        text_input = self.query_one("#text_input", Input)
        text = text_input.value.strip()
        
        if not text:
            self.notify("⚠️ Введите текст для анализа")
            return
        
        text_input.value = ""
        
        log = self.query_one("#text_log", RichLog)
        log.write(f"💬 Анализирую текст: '{text}'")
        
        @work
        async def analysis_task():
            try:
                result = await asyncio.to_thread(self.tux_core.analyze_text, text)
                
                if result["success"]:
                    log.write("✅ Анализ завершен:")
                    log.write(f"📊 Настроение: {result['sentiment']:.2f} (0-1, где 1 - позитивное)")
                    log.write(f"📈 Сложность: {result['complexity']:.2f} (0-1, где 1 - сложный)")
                    log.write(f"📏 Длина: {result['text_length']} символов, {result['words_count']} слов")
                    
                    # Интерпретация
                    sentiment_desc = "позитивный" if result['sentiment'] > 0.6 else "негативный" if result['sentiment'] < 0.4 else "нейтральный"
                    complexity_desc = "сложный" if result['complexity'] > 0.6 else "простой" if result['complexity'] < 0.4 else "средней сложности"
                    
                    log.write(f"🎯 Интерпретация: {sentiment_desc}, {complexity_desc}")
                    
                else:
                    log.write(f"❌ Ошибка анализа: {result.get('error', 'Неизвестная ошибка')}")
                    
            except Exception as e:
                log.write(f"❌ Исключение: {str(e)}")
        
        analysis_task()
    
    @on(Button.Pressed, "#demo_analyze")
    def on_demo_analyze(self):
        """Демонстрационный анализ"""
        sample_texts = [
            "Tux AI - это прекрасная нейронная сеть с 1000 нейронов!",
            "Я не очень доволен текущей ситуацией с искусственным интеллектом.",
            "Сложные математические вычисления требуют глубокого понимания алгоритмов.",
            "Простое предложение без особого смысла."
        ]
        
        import random
        text = random.choice(sample_texts)
        
        # Устанавливаем текст в input и запускаем анализ
        text_input = self.query_one("#text_input", Input)
        text_input.value = text
        self.on_analyze_text()
    
    @on(Button.Pressed, "#save_model")
    def on_save_model(self):
        """Сохранение модели"""
        log = self.query_one("#main_network_log", RichLog)
        log.write("💾 Сохраняю модель...")
        
        result = self.tux_core.save_model()
        
        if result["success"]:
            log.write("✅ Модель успешно сохранена!")
            log.write(f"📁 Путь: {result['path']}")
            self.notify("💾 Модель сохранена")
        else:
            log.write(f"❌ Ошибка сохранения: {result.get('error', 'Неизвестная ошибка')}")
            self.notify("❌ Ошибка сохранения")
    
    @on(Button.Pressed, "#load_model")
    def on_load_model(self):
        """Загрузка модели"""
        log = self.query_one("#main_network_log", RichLog)
        log.write("📥 Загружаю модель...")
        
        result = self.tux_core.load_model()
        
        if result["success"]:
            log.write("✅ Модель успешно загружена!")
            log.write(f"📁 Загружено из: {result['loaded_from']}")
            self._initialize_networks()
            self.notify("📥 Модель загружена")
        else:
            log.write(f"❌ Ошибка загрузки: {result.get('error', 'Неизвестная ошибка')}")
            self.notify("❌ Ошибка загрузки")
    
    def action_focus_neurons(self):
        self.query_one(TabbedContent).active = "neurons"
        self.notify("🧠 Переключено на нейроны")
    
    def action_focus_training(self):
        self.query_one(TabbedContent).active = "training"
        self.notify("🎓 Переключено на обучение")
    
    def action_focus_analysis(self):
        self.query_one(TabbedContent).active = "analysis"
        self.notify("🔍 Переключено на анализ")
    
    def action_refresh_stats(self):
        self._initialize_networks()
        self.notify("🔄 Статистика обновлена")

def main():
    """Запуск нейронного TUI"""
    try:
        app = NeuralTuxTUI()
        app.run()
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        print("🔧 Решение проблем:")
        print("1. Убедитесь что установлен PyTorch: pip install torch")
        print("2. Проверьте доступность GPU/CUDA")
        print("3. Запустите демо: python -c 'from src.core.tux_neural_network import demonstrate_tux_ai; demonstrate_tux_ai()'")

if __name__ == "__main__":
    main()