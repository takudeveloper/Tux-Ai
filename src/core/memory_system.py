"""
Система памяти Tux AI для сохранения контекста и обучения
"""

import sqlite3
import json
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class MemorySystem:
    """Система долговременной памяти для Tux AI"""
    
    def __init__(self, db_path: str = "data/memory/memory.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words=['и', 'в', 'на', 'с', 'по', 'у'])
        self._init_database()
        self._load_vectorizer()
    
    def _init_database(self):
        """Инициализация базы данных памяти"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица разговоров
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                user_message TEXT,
                ai_response TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                topic TEXT,
                importance INTEGER DEFAULT 1,
                embedding BLOB
            )
        ''')
        
        # Таблица знаний
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fact TEXT,
                category TEXT,
                source TEXT,
                confidence REAL DEFAULT 1.0,
                last_used DATETIME,
                usage_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица пользовательских предпочтений
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT DEFAULT 'default',
                preference_type TEXT,
                preference_value TEXT,
                strength REAL DEFAULT 1.0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_vectorizer(self):
        """Загрузка или создание векторизатора"""
        vectorizer_path = self.db_path.parent / "vectorizer.pkl"
        if vectorizer_path.exists():
            with open(vectorizer_path, 'rb') as f:
                self.vectorizer = pickle.load(f)
    
    def _save_vectorizer(self):
        """Сохранение векторизатора"""
        vectorizer_path = self.db_path.parent / "vectorizer.pkl"
        with open(vectorizer_path, 'wb') as f:
            pickle.dump(self.vectorizer, f)
    
    def save_conversation(self, session_id: str, user_message: str, ai_response: str, topic: str = None, importance: int = 1):
        """Сохранение разговора в память"""
        try:
            # Создаем embedding для семантического поиска
            combined_text = f"{user_message} {ai_response}"
            embedding = self._create_embedding(combined_text)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO conversations (session_id, user_message, ai_response, topic, importance, embedding)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (session_id, user_message, ai_response, topic, importance, pickle.dumps(embedding)))
            
            conn.commit()
            conn.close()
            
            # Обновляем векторизатор
            self._update_vectorizer(combined_text)
            
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения разговора: {e}")
            return False
    
    def _create_embedding(self, text: str) -> np.ndarray:
        """Создание embedding для текста"""
        try:
            # Простая реализация через TF-IDF
            embedding = self.vectorizer.transform([text]).toarray()[0]
            return embedding
        except:
            return np.zeros(1000)
    
    def _update_vectorizer(self, text: str):
        """Обновление векторизатора с новым текстом"""
        try:
            # Получаем все тексты для переобучения
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT user_message, ai_response FROM conversations')
            texts = []
            for row in cursor.fetchall():
                texts.append(f"{row[0]} {row[1]}")
            conn.close()
            
            # Добавляем новый текст
            texts.append(text)
            
            # Переобучаем векторизатор
            if len(texts) > 0:
                self.vectorizer.fit(texts)
                self._save_vectorizer()
                
        except Exception as e:
            print(f"⚠️ Ошибка обновления векторизатора: {e}")
    
    def get_relevant_context(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Получение релевантного контекста по запросу"""
        try:
            query_embedding = self._create_embedding(query)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, session_id, user_message, ai_response, topic, importance, embedding 
                FROM conversations 
                ORDER BY timestamp DESC 
                LIMIT 100
            ''')
            
            conversations = []
            for row in cursor.fetchall():
                conv_embedding = pickle.loads(row[6]) if row[6] else np.zeros(1000)
                similarity = cosine_similarity([query_embedding], [conv_embedding])[0][0]
                
                conversations.append({
                    'id': row[0],
                    'session_id': row[1],
                    'user_message': row[2],
                    'ai_response': row[3],
                    'topic': row[4],
                    'importance': row[5],
                    'similarity': similarity
                })
            
            conn.close()
            
            # Сортируем по релевантности
            conversations.sort(key=lambda x: x['similarity'], reverse=True)
            return conversations[:limit]
            
        except Exception as e:
            print(f"❌ Ошибка поиска контекста: {e}")
            return []
    
    def add_knowledge(self, fact: str, category: str, source: str, confidence: float = 1.0):
        """Добавление факта в базу знаний"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO knowledge (fact, category, source, confidence)
            VALUES (?, ?, ?, ?)
        ''', (fact, category, source, confidence))
        
        conn.commit()
        conn.close()
    
    def get_knowledge(self, category: str = None, min_confidence: float = 0.5) -> List[Dict[str, Any]]:
        """Получение знаний по категории"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if category:
            cursor.execute('''
                SELECT fact, category, source, confidence, last_used, usage_count
                FROM knowledge 
                WHERE category = ? AND confidence >= ?
                ORDER BY usage_count DESC, confidence DESC
            ''', (category, min_confidence))
        else:
            cursor.execute('''
                SELECT fact, category, source, confidence, last_used, usage_count
                FROM knowledge 
                WHERE confidence >= ?
                ORDER BY usage_count DESC, confidence DESC
            ''', (min_confidence,))
        
        knowledge = []
        for row in cursor.fetchall():
            knowledge.append({
                'fact': row[0],
                'category': row[1],
                'source': row[2],
                'confidence': row[3],
                'last_used': row[4],
                'usage_count': row[5]
            })
        
        conn.close()
        return knowledge
    
    def update_preference(self, preference_type: str, preference_value: str, user_id: str = 'default', strength: float = 1.0):
        """Обновление пользовательских предпочтений"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Проверяем существование предпочтения
        cursor.execute('''
            SELECT id, strength FROM user_preferences 
            WHERE user_id = ? AND preference_type = ?
        ''', (user_id, preference_type))
        
        existing = cursor.fetchone()
        
        if existing:
            # Обновляем существующее
            new_strength = min(1.0, existing[1] + strength)
            cursor.execute('''
                UPDATE user_preferences 
                SET preference_value = ?, strength = ? 
                WHERE id = ?
            ''', (preference_value, new_strength, existing[0]))
        else:
            # Создаем новое
            cursor.execute('''
                INSERT INTO user_preferences (user_id, preference_type, preference_value, strength)
                VALUES (?, ?, ?, ?)
            ''', (user_id, preference_type, preference_value, strength))
        
        conn.commit()
        conn.close()
    
    def get_user_profile(self, user_id: str = 'default') -> Dict[str, Any]:
        """Получение профиля пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT preference_type, preference_value, strength 
            FROM user_preferences 
            WHERE user_id = ? AND strength > 0.3
            ORDER BY strength DESC
        ''', (user_id,))
        
        preferences = {}
        for row in cursor.fetchall():
            preferences[row[0]] = {
                'value': row[1],
                'strength': row[2]
            }
        
        # Статистика разговоров
        cursor.execute('''
            SELECT COUNT(*) as total_conversations,
                   COUNT(DISTINCT topic) as unique_topics,
                   MAX(timestamp) as last_active
            FROM conversations 
            WHERE session_id LIKE ?
        ''', (f"{user_id}%",))
        
        stats_row = cursor.fetchone()
        stats = {
            'total_conversations': stats_row[0],
            'unique_topics': stats_row[1],
            'last_active': stats_row[2]
        }
        
        conn.close()
        
        return {
            'user_id': user_id,
            'preferences': preferences,
            'statistics': stats
        }
    
    def cleanup_old_memory(self, days_old: int = 30):
        """Очистка старой памяти"""
        cutoff_date = (datetime.now() - timedelta(days=days_old)).strftime('%Y-%m-%d %H:%M:%S')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Удаляем старые разговоры с низкой важностью
        cursor.execute('''
            DELETE FROM conversations 
            WHERE timestamp < ? AND importance < 2
        ''', (cutoff_date,))
        
        # Уменьшаем уверенность старых знаний
        cursor.execute('''
            UPDATE knowledge 
            SET confidence = confidence * 0.9 
            WHERE last_used < ? OR last_used IS NULL
        ''', (cutoff_date,))
        
        conn.commit()
        conn.close()