"""
Система обучения Tux AI
"""

import asyncio
from typing import List, Dict, Any
from pathlib import Path
import aiohttp
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime

class TrainingSystem:
    """Система обучения на интернет-данных и файлах"""
    
    def __init__(self, model_engine, db_path: str = "data/training.db"):
        self.model_engine = model_engine
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Инициализация базы данных обучения"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS training_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT,
                data_source TEXT,
                samples_processed INTEGER,
                loss REAL,
                duration REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_base (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT,
                content TEXT,
                topic TEXT,
                used_in_training BOOLEAN DEFAULT FALSE,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def train_on_topic(self, topic: str, max_pages: int = 3) -> Dict[str, Any]:
        """Обучение на данных из интернета по теме"""
        try:
            # Сбор данных
            collected_data = await self._collect_internet_data(topic, max_pages)
            
            if not collected_data:
                return {"success": False, "error": "Не удалось собрать данные"}
            
            # Объединяем все тексты
            training_text = "\n".join([item['content'] for item in collected_data])
            
            # Обучаем модель
            result = self.model_engine.train_on_text(training_text, epochs=2)
            
            if result["success"]:
                # Сохраняем сессию обучения
                self._save_training_session(topic, "internet", len(collected_data), result.get("loss", 0))
                
                # Сохраняем данные в базу знаний
                for item in collected_data:
                    self._save_to_knowledge_base(item['content'], topic, item['source'])
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _collect_internet_data(self, topic: str, max_pages: int) -> List[Dict]:
        """Сбор данных из интернета"""
        # Упрощенная версия сбора данных
        # В реальной реализации здесь будет парсинг сайтов
        
        # Заглушка с демо-данными
        demo_data = [
            {
                'source': 'demo_wikipedia',
                'content': f'''Статья о {topic}. {topic} - это интересная тема для изучения. 
                В современном мире {topic} играет важную роль. Многие аспекты {topic} 
                требуют дополнительного исследования и понимания.'''
            },
            {
                'source': 'demo_news',
                'content': f'''Новости о {topic}. Сегодня в сфере {topic} произошли важные события. 
                Эксперты отмечают рост интереса к {topic} среди широкой публики. 
                Перспективы развития {topic} выглядят многообещающе.'''
            },
            {
                'source': 'demo_research',
                'content': f'''Исследование {topic}. Ученые обнаружили новые факты о {topic}. 
                Проведенные эксперименты показывают, что {topic} имеет сложную природу. 
                Дальнейшее изучение {topic} может привести к важным открытиям.'''
            }
        ]
        
        # Имитация задержки сети
        await asyncio.sleep(2)
        
        return demo_data[:max_pages]
    
    def train_on_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """Обучение на файлах"""
        try:
            all_text = ""
            
            for file_path in file_paths:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        all_text += f.read() + "\n\n"
                except Exception as e:
                    print(f"❌ Ошибка чтения файла {file_path}: {e}")
            
            if not all_text.strip():
                return {"success": False, "error": "Нет данных для обучения"}
            
            result = self.model_engine.train_on_text(all_text, epochs=3)
            
            if result["success"]:
                self._save_training_session("files_training", "files", len(file_paths), result.get("loss", 0))
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _save_training_session(self, topic: str, data_source: str, samples: int, loss: float):
        """Сохранение сессии обучения"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO training_sessions (topic, data_source, samples_processed, loss)
            VALUES (?, ?, ?, ?)
        ''', (topic, data_source, samples, loss))
        
        conn.commit()
        conn.close()
    
    def _save_to_knowledge_base(self, content: str, topic: str, source: str):
        """Сохранение в базу знаний"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO knowledge_base (content, topic, source)
            VALUES (?, ?, ?)
        ''', (content, topic, source))
        
        conn.commit()
        conn.close()
    
    def get_training_history(self, limit: int = 10) -> List[Dict]:
        """Получение истории обучения"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT topic, data_source, samples_processed, loss, timestamp
            FROM training_sessions 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'topic': row[0],
                'source': row[1],
                'samples': row[2],
                'loss': row[3],
                'timestamp': row[4]
            })
        
        conn.close()
        return history