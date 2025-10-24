"""
Движок ИИ модели для Tux AI
Реализует загрузку моделей, генерацию и базовое обучение
"""

import torch
import torch.nn as nn
from transformers import GPT2LMHeadModel, GPT2Tokenizer, TextDataset, DataCollatorForLanguageModeling
from transformers import Trainer, TrainingArguments
import os
from pathlib import Path
from typing import List, Dict, Any
import json

class TuxModelEngine:
    """Движок для работы с ИИ моделями"""
    
    def __init__(self, model_dir: str = "data/models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        self.model = None
        self.tokenizer = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.is_loaded = False
        
        # Конфигурация модели
        self.config = {
            "max_length": 200,
            "temperature": 0.8,
            "top_k": 50,
            "top_p": 0.9,
            "repetition_penalty": 1.1
        }
    
    def load_model(self, model_name: str = "sberbank-ai/rugpt3small_based_on_gpt2"):
        """Загрузка модели"""
        try:
            print(f"🧠 Загружаю модель: {model_name}")
            
            self.tokenizer = GPT2Tokenizer.from_pretrained(model_name)
            self.model = GPT2LMHeadModel.from_pretrained(model_name)
            
            # Настройка токенизатора
            self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Перенос модели на устройство
            self.model.to(self.device)
            self.model.eval()
            
            self.is_loaded = True
            print(f"✅ Модель загружена на {self.device}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка загрузки модели: {e}")
            self.is_loaded = False
            return False
    
    def generate_response(self, prompt: str, **kwargs) -> str:
        """Генерация ответа"""
        if not self.is_loaded:
            return "⚠️ Модель не загружена. Загрузите модель сначала."
        
        try:
            # Объединяем конфигурацию с переданными параметрами
            config = {**self.config, **kwargs}
            
            # Токенизация промпта
            inputs = self.tokenizer.encode(prompt, return_tensors="pt").to(self.device)
            
            # Генерация
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_length=len(inputs[0]) + config["max_length"],
                    temperature=config["temperature"],
                    top_k=config["top_k"],
                    top_p=config["top_p"],
                    repetition_penalty=config["repetition_penalty"],
                    pad_token_id=self.tokenizer.eos_token_id,
                    do_sample=True,
                    num_return_sequences=1
                )
            
            # Декодирование ответа
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Удаляем промпт из ответа
            if response.startswith(prompt):
                response = response[len(prompt):].strip()
            
            return response
            
        except Exception as e:
            return f"❌ Ошибка генерации: {str(e)}"
    
    def train_on_text(self, text: str, epochs: int = 3):
        """Базовое обучение на тексте"""
        if not self.is_loaded:
            return {"success": False, "error": "Модель не загружена"}
        
        try:
            # Сохраняем текст в временный файл
            temp_file = self.model_dir / "temp_training.txt"
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(text)
            
            # Создаем dataset
            train_dataset = TextDataset(
                tokenizer=self.tokenizer,
                file_path=str(temp_file),
                block_size=128
            )
            
            data_collator = DataCollatorForLanguageModeling(
                tokenizer=self.tokenizer,
                mlm=False
            )
            
            # Настройки обучения
            training_args = TrainingArguments(
                output_dir=str(self.model_dir / "checkpoints"),
                overwrite_output_dir=True,
                num_train_epochs=epochs,
                per_device_train_batch_size=2,
                save_steps=100,
                save_total_limit=2,
                prediction_loss_only=True,
                logging_steps=10,
            )
            
            # Обучение
            trainer = Trainer(
                model=self.model,
                args=training_args,
                data_collator=data_collator,
                train_dataset=train_dataset,
            )
            
            # Запуск обучения
            trainer.train()
            
            # Сохранение модели
            trainer.save_model()
            
            # Удаляем временный файл
            temp_file.unlink()
            
            return {"success": True, "epochs": epochs, "loss": trainer.state.log_history[-1]['loss']}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def save_model(self, path: str):
        """Сохранение модели"""
        if self.is_loaded:
            save_path = self.model_dir / path
            self.model.save_pretrained(save_path)
            self.tokenizer.save_pretrained(save_path)
            return True
        return False
    
    def load_custom_model(self, path: str):
        """Загрузка кастомной модели"""
        try:
            model_path = self.model_dir / path
            self.tokenizer = GPT2Tokenizer.from_pretrained(str(model_path))
            self.model = GPT2LMHeadModel.from_pretrained(str(model_path))
            self.model.to(self.device)
            self.model.eval()
            self.is_loaded = True
            return True
        except Exception as e:
            print(f"❌ Ошибка загрузки кастомной модели: {e}")
            return False

class SimpleFallbackModel:
    """Простая модель-заглушка когда основная не доступна"""
    
    def __init__(self):
        self.responses = [
            "Привет! Я Tux AI, ваша локальная ИИ система. 🐧",
            "Отличный вопрос! В полной версии я смогу дать более развернутый ответ.",
            "Tux AI готов к работе! Загрузите модель для расширенных возможностей.",
            "Интересный запрос! Я обучаюсь на ваших данных и становлюсь умнее.",
            "Пингвины одобряют ваше любопытство! 🐧",
            "В этом демо-режиме я показываю базовые возможности. Полная версия поразит вас!",
            "Работаю над вашим запросом... В полной версии здесь будет интеллектуальный ответ.",
            "Tux AI учится! Каждое взаимодействие делает меня лучше.",
        ]
    
    def generate_response(self, prompt: str, **kwargs) -> str:
        import random
        return random.choice(self.responses)
    
    def train_on_text(self, text: str, epochs: int = 3):
        return {"success": True, "message": "Обучение в демо-режиме", "epochs": epochs}