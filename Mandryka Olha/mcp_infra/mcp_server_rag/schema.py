from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class RAGSearchRequest(BaseModel):
    query: str = Field(description="Пошуковий запит")
    k: int = Field(default=5, description="Кількість результатів для повернення")
    collection_name: str = Field(default="karpaty_knowledge", description="Назва колекції для пошуку")
    where: Optional[Dict[str, Any]] = Field(default=None, description="Фільтри для пошуку")

class RAGSearchResponse(BaseModel):
    query: str = Field(description="Оригінальний запит")
    chunks: List[str] = Field(description="Знайдені текстові фрагменти")
    count: int = Field(description="Кількість знайдених результатів")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Метадані пошуку")

class RAGAnalysisRequest(BaseModel):
    query: str = Field(description="Оригінальний запит користувача")
    chunks: List[str] = Field(description="Знайдені фрагменти для аналізу")
    analysis_type: str = Field(default="routes", description="Тип аналізу: routes, safety, general")
    preferences: List[str] = Field(default_factory=list, description="Вподобання користувача")

class RAGAnalysisResponse(BaseModel):
    analysis_type: str = Field(description="Тип проведеного аналізу")
    structured_data: Dict[str, Any] = Field(description="Структуровані дані з аналізу")
    summary: str = Field(description="Стислий опис результатів")
    confidence: float = Field(description="Рівень впевненості в результатах (0-1)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Додаткові метадані")


class RAGSafetySearchRequest(BaseModel):
    query: str = Field(description="Пошуковий запит (наприклад назва маршруту або тип небезпеки)")
    k: int = Field(default=5, description="Кількість результатів")