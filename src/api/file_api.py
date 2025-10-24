# file_api.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn
from typing import List, Optional
from file_processor import FileProcessor

app = FastAPI(title="Tux AI File API")

# CORS для веб-интерфейса
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

file_processor = FileProcessor()

class SearchRequest(BaseModel):
    query: str

class FileInfoResponse(BaseModel):
    id: str
    filename: str
    original_name: str
    file_size: int
    file_type: str
    upload_time: str
    processed: bool
    chunks_count: int

@app.post("/api/v1/upload")
async def upload_file(file: UploadFile = File(...)):
    """Загрузка файла"""
    try:
        content = await file.read()
        result = file_processor.save_uploaded_file(content, file.filename)
        
        if result["success"]:
            return {
                "success": True,
                "message": "Файл успешно загружен",
                "data": result
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/files", response_model=List[FileInfoResponse])
async def list_files(limit: int = 50):
    """Список загруженных файлов"""
    files = file_processor.list_files(limit)
    return files

@app.get("/api/v1/files/{file_id}")
async def get_file_info(file_id: str):
    """Информация о конкретном файле"""
    file_info = file_processor.get_file_info(file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="Файл не найден")
    return file_info

@app.get("/api/v1/files/{file_id}/download")
async def download_file(file_id: str):
    """Скачивание файла"""
    file_info = file_processor.get_file_info(file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="Файл не найден")
    
    return FileResponse(
        file_info["file_path"],
        filename=file_info["original_name"],
        media_type=file_info["mime_type"]
    )

@app.delete("/api/v1/files/{file_id}")
async def delete_file(file_id: str):
    """Удаление файла"""
    # Реализация удаления файла
    return {"success": True, "message": "Файл удален"}

@app.post("/api/v1/search")
async def search_files(request: SearchRequest):
    """Поиск по файлам"""
    results = file_processor.search_in_files(request.query)
    return {
        "query": request.query,
        "results": results,
        "count": len(results)
    }

@app.get("/api/v1/stats")
async def get_stats():
    """Статистика файлов"""
    files = file_processor.list_files(limit=1000)
    total_size = sum(f["file_size"] for f in files)
    file_types = {}
    
    for file in files:
        file_type = file["file_type"]
        file_types[file_type] = file_types.get(file_type, 0) + 1
    
    return {
        "total_files": len(files),
        "total_size_bytes": total_size,
        "total_size_mb": total_size / (1024 * 1024),
        "file_types": file_types
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)