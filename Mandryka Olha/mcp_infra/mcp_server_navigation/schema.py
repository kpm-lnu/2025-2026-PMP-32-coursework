
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from typing_extensions import Annotated

class RoutingRequest(BaseModel):
    start: Annotated[List[float], Field(min_length=2, max_length=2)] = Field(
        ..., 
        description="Координати початку маршруту: [lon, lat]"
    )

    end: Annotated[List[float], Field(min_length=2, max_length=2)] = Field(
        ..., 
        description="Координати кінця маршруту: [lon, lat]"
    )

    routeType: Literal[
        "foot_fast",
        "foot_hiking",
        "bike_road",
        "bike_mountain",
        "car_fast",
        "car_fast_traffic",
        "car_short"
    ] = Field(
        "foot_hiking",
        description="Тип маршруту"
    )

    lang: Optional[Literal["en", "uk"]] = Field(
        "uk",
        description="Мова відповіді"
    )

    format: Optional[Literal["geojson", "polyline", "polyline6"]] = Field(
        "geojson",
        description="Формат геометрії маршруту"
    )

    avoidHighways: Optional[bool] = Field(
        False,
        description="Уникати автомагістралей"
    )

    departure: Optional[str] = Field(
        None,
        description="Час відправлення у форматі ISO-8601 (наприклад, 2025-12-23T10:00:00)"
    )

    waypoints: Optional[List[Annotated[List[float], Field(min_length=2, max_length=2)]]] = Field(
        None,
        max_length=15,
        description="Проміжні точки (до 15): кожна — [lon, lat]"
    )