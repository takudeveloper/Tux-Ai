"""
Плагин анализа кода для Tux AI
"""

import ast
import tokenize
from io import StringIO
from typing import List, Dict, Any
from src.core.plugin_system import TuxPlugin

class CodeAnalyzerPlugin(TuxPlugin):
    """Плагин для анализа и обработки кода"""
    
    def __init__(self, plugin_manager):
        super().__init__(plugin_manager)
        self.name = "CodeAnalyzer"
        self.version = "1.0.0"
    
    def get_capabilities(self) -> List[str]:
        return [
            "analyze_python_code",
            "syntax_check", 
            "code_complexity",
            "suggest_improvements",
            "extract_functions"
        ]
    
    def execute(self, capability: str, **kwargs) -> Any:
        if capability == "analyze_python_code":
            return self.analyze_python_code(**kwargs)
        elif capability == "syntax_check":
            return self.syntax_check(**kwargs)
        elif capability == "code_complexity":
            return self.calculate_complexity(**kwargs)
        elif capability == "suggest_improvements":
            return self.suggest_improvements(**kwargs)
        elif capability == "extract_functions":
            return self.extract_functions(**kwargs)
        
        return None
    
    def analyze_python_code(self, code: str) -> Dict[str, Any]:
        """Анализ Python кода"""
        try:
            # Парсим AST
            tree = ast.parse(code)
            
            analysis = {
                'valid': True,
                'lines': len(code.splitlines()),
                'functions': [],
                'classes': [],
                'imports': [],
                'issues': []
            }
            
            # Анализируем AST
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    analysis['functions'].append({
                        'name': node.name,
                        'line': node.lineno,
                        'args': len(node.args.args),
                        'docstring': ast.get_docstring(node)
                    })
                
                elif isinstance(node, ast.ClassDef):
                    analysis['classes'].append({
                        'name': node.name,
                        'line': node.lineno,
                        'methods': len([n for n in node.body if isinstance(n, ast.FunctionDef)])
                    })
                
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    analysis['imports'].append(ast.unparse(node))
            
            # Проверяем сложность
            complexity = self.calculate_complexity(code)
            analysis['complexity'] = complexity
            
            return analysis
            
        except SyntaxError as e:
            return {
                'valid': False,
                'error': f"Синтаксическая ошибка: {e}",
                'line': e.lineno,
                'offset': e.offset
            }
    
    def syntax_check(self, code: str) -> Dict[str, Any]:
        """Проверка синтаксиса"""
        try:
            ast.parse(code)
            return {'valid': True, 'message': '✅ Синтаксис корректен'}
        except SyntaxError as e:
            return {
                'valid': False,
                'error': str(e),
                'line': e.lineno,
                'offset': e.offset
            }
    
    def calculate_complexity(self, code: str) -> Dict[str, Any]:
        """Расчет сложности кода"""
        try:
            tree = ast.parse(code)
            
            metrics = {
                'cyclomatic_complexity': 1,  # Базовая сложность
                'lines_of_code': len(code.splitlines()),
                'function_count': 0,
                'class_count': 0,
                'average_function_length': 0
            }
            
            # Считаем функции и классы
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    metrics['function_count'] += 1
                    # Простая оценка сложности
                    metrics['cyclomatic_complexity'] += len([
                        n for n in ast.walk(node) 
                        if isinstance(n, (ast.If, ast.While, ast.For, ast.ExceptHandler))
                    ])
                
                elif isinstance(node, ast.ClassDef):
                    metrics['class_count'] += 1
            
            if metrics['function_count'] > 0:
                metrics['average_function_length'] = metrics['lines_of_code'] / metrics['function_count']
            
            # Оценка сложности
            if metrics['cyclomatic_complexity'] < 10:
                complexity_level = "Низкая"
            elif metrics['cyclomatic_complexity'] < 20:
                complexity_level = "Средняя"
            else:
                complexity_level = "Высокая"
            
            metrics['complexity_level'] = complexity_level
            
            return metrics
            
        except Exception as e:
            return {'error': f"Ошибка анализа сложности: {e}"}
    
    def suggest_improvements(self, code: str) -> List[str]:
        """Предложения по улучшению кода"""
        suggestions = []
        
        try:
            tree = ast.parse(code)
            
            # Проверяем длину функций
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    function_lines = node.end_lineno - node.lineno if node.end_lineno else 0
                    if function_lines > 50:
                        suggestions.append(f"Функция '{node.name}' слишком длинная ({function_lines} строк). Рекомендуется разбить на smaller функции.")
            
            # Проверяем имена переменных
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                    if len(node.id) == 1 and node.id not in ['i', 'j', 'k', 'x', 'y', 'z']:
                        suggestions.append(f"Однобуквенное имя переменной '{node.id}' может быть неинформативным")
            
            # Проверяем документацию
            if not any(isinstance(node, ast.Expr) and isinstance(node.value, ast.Str) 
                      for node in tree.body):
                suggestions.append("Добавьте docstring для модуля")
            
            return suggestions
            
        except Exception as e:
            return [f"Ошибка анализа: {e}"]
    
    def extract_functions(self, code: str) -> List[Dict[str, Any]]:
        """Извлечение функций из кода"""
        try:
            tree = ast.parse(code)
            functions = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    function_code = ast.get_source_segment(code, node)
                    functions.append({
                        'name': node.name,
                        'code': function_code,
                        'line': node.lineno,
                        'docstring': ast.get_docstring(node)
                    })
            
            return functions
            
        except Exception as e:
            return [{'error': f"Ошибка извлечения функций: {e}"}]