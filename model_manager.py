# model_manager.py
import torch
import os
import json
from typing import Dict, Any, Optional
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

class ModelManager:
    """Менеджер для управления полной и урезанной версиями модели"""
    
    def __init__(self, config_path: str = "model_config.json"):
        self.config_path = config_path
        self.models = {}  # Кэш загруженных моделей
        self.current_mode = "full"  # Режим по умолчанию
        
        # Создаем директории если нужно
        os.makedirs("models/full", exist_ok=True)
        os.makedirs("models/lite", exist_ok=True)
        os.makedirs("checkpoints", exist_ok=True)
    
    def load_model(self, mode: str = "full") -> Any:
        """Загрузка модели в указанном режиме"""
        if mode in self.models:
            return self.models[mode]
        
        try:
            if mode == "full":
                model_path = "models/full"
            else:
                model_path = "models/lite"
            
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Модель в режиме {mode} не найдена")
            
            # Здесь должна быть логика загрузки вашей модели
            from tux_model import TuxAIModel, TuxModelConfig
            
            config = TuxModelConfig.load("models/full/config.json")
            model = TuxAIModel.from_pretrained(model_path, mode=mode)
            
            self.models[mode] = model
            self.current_mode = mode
            
            return model
            
        except Exception as e:
            print(f"Ошибка загрузки модели {mode}: {e}")
            return None
    
    def switch_mode(self, new_mode: str):
        """Переключение между полной и урезанной версиями"""
        if new_mode not in ["full", "lite"]:
            raise ValueError("Режим должен быть 'full' или 'lite'")
        
        if new_mode == self.current_mode:
            return True
        
        # Выгружаем текущую модель если она загружена
        if self.current_mode in self.models:
            del self.models[self.current_mode]
        
        # Загружаем новую модель
        success = self.load_model(new_mode) is not None
        return success
    
    def create_lite_version(self, compression_ratio: float = 0.5):
        """Создание урезанной версии из полной"""
        full_model = self.load_model("full")
        if full_model is None:
            raise ValueError("Полная версия модели не загружена")
        
        # Конвертация в lite версию
        lite_model = full_model.convert_to_lite()
        
        # Сохранение lite версии
        lite_model.save_pretrained("models/lite")
        
        # Обновление кэша
        self.models["lite"] = lite_model
        
        return True
    
    def get_model_info(self) -> Dict[str, Any]:
        """Получение информации о загруженных моделях"""
        info = {
            "current_mode": self.current_mode,
            "loaded_models": list(self.models.keys()),
            "model_sizes": {}
        }
        
        for mode, model in self.models.items():
            if hasattr(model, 'parameters'):
                param_count = sum(p.numel() for p in model.parameters())
                info["model_sizes"][mode] = {
                    "parameters": f"{param_count:,}",
                    "size_mb": param_count * 4 / (1024 ** 2)  # Примерный размер в MB
                }
        
        return info

# FastAPI для управления моделью
app = FastAPI(title="Tux AI Model Manager")
model_manager = ModelManager()

class GenerationRequest(BaseModel):
    prompt: str
    max_length: int = 100
    temperature: float = 0.8
    top_k: int = 50
    top_p: float = 0.9
    mode: str = "full"

class TrainingRequest(BaseModel):
    queries: List[str]
    epochs: int = 3
    batch_size: int = 4

@app.post("/v1/generate")
async def generate_text(request: GenerationRequest):
    """Генерация текста"""
    try:
        model = model_manager.load_model(request.mode)
        if model is None:
            raise HTTPException(status_code=404, detail="Модель не найдена")
        
        # Токенизация промпта
        tokens = model.tokenizer.encode(request.prompt)
        input_ids = torch.tensor([tokens])
        
        # Генерация
        generated = model.generate(
            input_ids,
            max_length=request.max_length,
            temperature=request.temperature,
            top_k=request.top_k,
            top_p=request.top_p
        )
        
        # Декодирование
        response_text = model.tokenizer.decode(generated[0].tolist())
        
        return {
            "generated_text": response_text,
            "mode": request.mode,
            "tokens_generated": len(generated[0]) - len(tokens)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/train")
async def train_model(request: TrainingRequest):
    """Обучение модели на новых данных"""
    try:
        from tux_training import TuxTrainingEngine
        from internet_search import AdvancedInternetSearch
        
        model = model_manager.load_model("full")
        if model is None:
            raise HTTPException(status_code=404, detail="Модель не найдена")
        
        # Инициализация движка обучения
        tokenizer = model.tokenizer
        kb = AdvancedInternetSearch()
        
        training_engine = TuxTrainingEngine(model, tokenizer, kb)
        
        # Запуск обучения
        result = training_engine.train_on_internet_data(
            request.queries,
            epochs=request.epochs,
            batch_size=request.batch_size
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/model/info")
async def get_model_info():
    """Получение информации о модели"""
    return model_manager.get_model_info()

@app.post("/v1/model/switch/{mode}")
async def switch_model_mode(mode: str):
    """Переключение режима модели"""
    success = model_manager.switch_mode(mode)
    return {"success": success, "new_mode": mode}

@app.post("/v1/model/create-lite")
async def create_lite_version():
    """Создание урезанной версии модели"""
    success = model_manager.create_lite_version()
    return {"success": success}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)