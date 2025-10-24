# internet_search.py
import requests
from bs4 import BeautifulSoup
import sqlite3
from urllib.parse import urljoin, urlparse
import time
from datetime import datetime
from typing import List, Dict, Optional
import re

class AdvancedInternetSearch:
    """Продвинутая система поиска в интернете с множеством источников"""
    
    def __init__(self, db_path: str = "tux_knowledge.db"):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self._init_database()
    
    def _init_database(self):
        """Инициализация расширенной базы данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Основная таблица знаний
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_url TEXT,
                title TEXT,
                content TEXT,
                topic TEXT,
                language TEXT DEFAULT 'ru',
                quality_score REAL DEFAULT 1.0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                embedding BLOB
            )
        ''')
        
        # Таблица для кэширования запросов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_cache (
                query_hash TEXT PRIMARY KEY,
                query_text TEXT,
                results_json TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица источников
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sources (
                domain TEXT PRIMARY KEY,
                reliability_score REAL DEFAULT 0.5,
                last_accessed DATETIME,
                access_count INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def search_multiple_sources(self, query: str, max_results: int = 5) -> List[Dict]:
        """Поиск по множеству источников"""
        all_results = []
        
        # Поиск через различные методы
        search_methods = [
            self._search_duckduckgo,
            self._search_google_news,
            self._search_wikipedia
        ]
        
        for method in search_methods:
            try:
                results = method(query, max_results=max_results // 2)
                all_results.extend(results)
                time.sleep(1)  # Задержка между запросами
            except Exception as e:
                print(f"Ошибка в {method.__name__}: {e}")
                continue
        
        # Удаление дубликатов и сортировка по релевантности
        unique_results = self._deduplicate_results(all_results)
        return unique_results[:max_results]
    
    def _search_duckduckgo(self, query: str, max_results: int = 3) -> List[Dict]:
        """Поиск через DuckDuckGo"""
        try:
            url = "https://html.duckduckgo.com/html/"
            params = {
                'q': query,
                'kl': 'ru-ru'
            }
            
            response = self.session.post(url, data=params, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            results = []
            for result in soup.find_all('div', class_='result')[:max_results]:
                link_elem = result.find('a', class_='result__a')
                if not link_elem:
                    continue
                
                title = link_elem.get_text()
                relative_url = link_elem.get('href')
                
                if not relative_url:
                    continue
                
                # DuckDuckGo возвращает редиректные ссылки
                actual_url = self._extract_actual_url(relative_url)
                
                if actual_url:
                    content = self._extract_page_content(actual_url)
                    if content:
                        results.append({
                            'title': title,
                            'url': actual_url,
                            'content': content[:1000],  # Ограничение длины
                            'source': 'duckduckgo'
                        })
            
            return results
            
        except Exception as e:
            print(f"Ошибка DuckDuckGo поиска: {e}")
            return []
    
    def _search_google_news(self, query: str, max_results: int = 3) -> List[Dict]:
        """Поиск через Google News"""
        try:
            url = "https://news.google.com/rss/search"
            params = {
                'q': query,
                'hl': 'ru',
                'gl': 'RU',
                'ceid': 'RU:ru'
            }
            
            response = self.session.get(url, params=params, timeout=15)
            soup = BeautifulSoup(response.content, 'xml')
            
            results = []
            for item in soup.find_all('item')[:max_results]:
                title = item.find('title').get_text()
                link = item.find('link').get_text()
                
                content = self._extract_page_content(link)
                if content:
                    results.append({
                        'title': title,
                        'url': link,
                        'content': content[:800],
                        'source': 'google_news'
                    })
            
            return results
            
        except Exception as e:
            print(f"Ошибка Google News поиска: {e}")
            return []
    
    def _search_wikipedia(self, query: str, max_results: int = 2) -> List[Dict]:
        """Поиск в Wikipedia"""
        try:
            url = "https://ru.wikipedia.org/w/api.php"
            params = {
                'action': 'query',
                'list': 'search',
                'srsearch': query,
                'format': 'json',
                'srlimit': max_results
            }
            
            response = self.session.get(url, params=params, timeout=15)
            data = response.json()
            
            results = []
            for item in data.get('query', {}).get('search', [])[:max_results]:
                page_id = item['pageid']
                title = item['title']
                
                # Получаем контент страницы
                content_url = "https://ru.wikipedia.org/w/api.php"
                content_params = {
                    'action': 'query',
                    'prop': 'extracts',
                    'pageids': page_id,
                    'explaintext': True,
                    'format': 'json'
                }
                
                content_response = self.session.get(content_url, params=content_params)
                content_data = content_response.json()
                
                page_content = content_data['query']['pages'][str(page_id)].get('extract', '')
                
                if page_content:
                    results.append({
                        'title': title,
                        'url': f"https://ru.wikipedia.org/wiki/{title.replace(' ', '_')}",
                        'content': page_content[:1200],
                        'source': 'wikipedia'
                    })
            
            return results
            
        except Exception as e:
            print(f"Ошибка Wikipedia поиска: {e}")
            return []
    
    def _extract_actual_url(self, duckduckgo_url: str) -> Optional[str]:
        """Извлечение реального URL из DuckDuckGo редиректа"""
        try:
            response = self.session.get(duckduckgo_url, allow_redirects=True, timeout=10)
            return response.url
        except:
            return None
    
    def _extract_page_content(self, url: str) -> Optional[str]:
        """Извлечение основного контента со страницы"""
        try:
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Удаление ненужных элементов
            for element in soup(['script', 'style', 'nav', 'header', 'footer']):
                element.decompose()
            
            # Поиск основного контента
            content_selectors = [
                'article',
                '.content',
                '.main-content',
                '#content',
                '.post-content',
                '.entry-content',
                'main'
            ]
            
            content = None
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content = content_elem.get_text()
                    break
            
            # Если не нашли по селекторам, берем body
            if not content:
                content = soup.find('body').get_text() if soup.find('body') else ""
            
            # Очистка текста
            content = ' '.join(content.split())
            content = re.sub(r'\s+', ' ', content)
            
            return content.strip() if content else None
            
        except Exception as e:
            print(f"Ошибка извлечения контента {url}: {e}")
            return None
    
    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """Удаление дубликатов и сортировка по релевантности"""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            if result['url'] not in seen_urls:
                seen_urls.add(result['url'])
                unique_results.append(result)
        
        # Сортировка по длине контента (грубый показатель качества)
        unique_results.sort(key=lambda x: len(x.get('content', '')), reverse=True)
        return unique_results
    
    def store_search_results(self, query: str, results: List[Dict]):
        """Сохранение результатов поиска в базу данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for result in results:
            cursor.execute('''
                INSERT INTO knowledge (source_url, title, content, topic)
                VALUES (?, ?, ?, ?)
            ''', (result['url'], result['title'], result['content'], query))
        
        conn.commit()
        conn.close()