from __future__ import annotations

from typing import List, Optional, Literal, Dict
from pydantic import BaseModel, Field


class WeatherRequest(BaseModel):
    location: Optional[str] = Field(
        None, description="Назва місця/локації (опціонально)"
    )
    lon: Optional[float] = Field(
        None, description="Довгота (longitude), наприклад 24.0"
    )
    lat: Optional[float] = Field(
        None, description="Широта (latitude), наприклад 48.0"
    )
    days: int = Field(
        3, ge=1, le=16, description="Кількість днів прогнозу"
    )
    units: Literal["metric", "imperial"] = Field(
        "metric", description="Одиниці вимірювання"
    )


class WeatherDataPoint(BaseModel):
    date: str
    temperature: Optional[float]
    rain_mm: Optional[float]
    wind_m_s: Optional[float]
    description: Optional[str]


class WeatherDataResponse(BaseModel):
    location: str
    days: int
    data: List[WeatherDataPoint]
    source: str = "OpenWeatherMap (forecast)"


class Criterion(BaseModel):
    factor: Literal[
        "rain", "wind", "temperature", "sun", "fog", "snow"
    ] = Field(..., description="Фактор погоди")
    relation: Literal[
        "prefer", "avoid", "neutral"
    ] = Field("neutral", description="Ставлення до фактора")
    importance: Literal[
        "high", "medium", "low"
    ] = Field("medium", description="Важливість фактора")


class AHPRequest(BaseModel):
    criteria: List[Criterion] = Field(
        ..., min_items=1, description="Список критеріїв для AHP"
    )


class AHPConsistency(BaseModel):
    lambda_max: float
    CI: float
    CR: float
    is_consistent: bool


class AHPResultResponse(BaseModel):
    weights: Dict[str, float]
    consistency: AHPConsistency


class ScoredDay(BaseModel):
    score: float
    day: WeatherDataPoint


class RankDaysRequest(BaseModel):
    forecast_data: List[WeatherDataPoint] = Field(..., description="Дані прогнозу погоди")
    criteria: List[Criterion] = Field(..., description="Критерії AHP")


class RankDaysResponse(BaseModel):
    best_day: WeatherDataPoint
    scored_days: List[ScoredDay]
