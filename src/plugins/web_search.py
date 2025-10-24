"""
Плагин веб-поиска для Tux AI
"""

import aiohttp
import asyncio
from bs4 import BeautifulSoup
from urllib.parse import quote
from typing import List, Dict, Any
from src.core.plugin_system import TuxPlugin

class WebSearchPlugin(TuxPlugin):
    """Плагин для поиска информации в интернете"""
    
    def __init__(self, plugin_manager):
        super().__init__(plugin_manager)
        self.name = "WebSearch"
        self.version = "1.1.0"
        self.session = None
    
    def get_capabilities(self) -> List[str]:
        return ["web_search", "get_news", "find_information"]
    
    async def _create_session(self):
        """Создание aiohttp сессии"""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                headers={
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
            )
    
    async def execute(self, capability: str, **kwargs) -> Any:
        await self._create_session()
        
        if capability == "web_search":
            return await self.web_search(**kwargs)
        elif capability == "get_news":
            return await self.get_news(**kwargs)
        elif capability == "find_information":
            return await self.find_information(**kwargs)
        
        return None
    
    async def web_search(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Поиск в интернете"""
        try:
            # Используем DuckDuckGo через HTML
            search_url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
            
            async with self.session.get(search_url) as response:
                html = await response.text()
            
            soup = BeautifulSoup(html, 'html.parser')
            results = []
            
            for result in soup.find_all('div', class_='result')[:max_results]:
                link_elem = result.find('a', class_='result__a')
                if link_elem:
                    title = link_elem.get_text()
                    # DuckDuckGo дает редиректные ссылки
                    href = link_elem.get('href', '')
                    
                    # Пытаемся получить описание
                    desc_elem = result.find('a', class_='result__snippet')
                    description = desc_elem.get_text() if desc_elem else ""
                    
                    results.append({
                        'title': title,
                        'url': href,
                        'description': description
                    })
            
            return results
            
        except Exception as e:
            return [{"error": f"Ошибка поиска: {str(e)}"}]
    
    async def get_news(self, topic: str = None, max_news: int = 5) -> List[Dict[str, str]]:
        """Получение новостей"""
        try:
            query = topic or "новости"
            search_url = f"https://news.google.com/rss/search?q={quote(query)}&hl=ru&gl=RU&ceid=RU:ru"
            
            async with self.session.get(search_url) as response:
                xml_content = await response.text()
            
            soup = BeautifulSoup(xml_content, 'xml')
            news_items = []
            
            for item in soup.find_all('item')[:max_news]:
                title = item.find('title').get_text()
                link = item.find('link').get_text()
                pub_date = item.find('pubDate').get_text() if item.find('pubDate') else ""
                
                news_items.append({
                    'title': title,
                    'url': link,
                    'date': pub_date,
                    'source': 'Google News'
                })
            
            return news_items
            
        except Exception as e:
            return [{"error": f"Ошибка получения новостей: {str(e)}"}]
    
    async def find_information(self, topic: str, sources: List[str] = None) -> Dict[str, Any]:
        """Поиск информации из различных источников"""
        results = {
            'topic': topic,
            'sources': {},
            'summary': ''
        }
        
        # Поиск в разных источниках
        search_tasks = []
        
        if not sources or 'web' in sources:
            search_tasks.append(self.web_search(topic, 3))
        
        if not sources or 'news' in sources:
            search_tasks.append(self.get_news(topic, 3))
        
        # Выполняем все поиски параллельно
        search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        # Обрабатываем результаты
        for i, result in enumerate(search_results):
            if isinstance(result, Exception):
                results['sources'][f'source_{i}'] = {'error': str(result)}
            else:
                results['sources'][f'source_{i}'] = result
        
        # Создаем краткое summary
        all_texts = []
        for source_name, source_data in results['sources'].items():
            if isinstance(source_data, list):
                for item in source_data:
                    if 'title' in item:
                        all_texts.append(item['title'])
                    if 'description' in item:
                        all_texts.append(item['description'])
        
        if all_texts:
            results['summary'] = " ".join(all_texts)[:500] + "..."
        
        return results
    
    async def on_enable(self):
        """При включении плагина"""
        await self._create_session()
        print("🔍 Плагин веб-поиска активирован")
    
    async def on_disable(self):
        """При выключении плагина"""
        if self.session:
            await self.session.close()
            self.session = None