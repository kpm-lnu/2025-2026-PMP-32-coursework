from pydantic import BaseModel, Field
from typing import Optional


class CalendarDayEventRequest(BaseModel):
    title: str = Field(
        ..., description="Назва події (наприклад: Похід A–B–A — день 2)"
    )

    date: str = Field(
        ..., description="Дата походу у форматі YYYY-MM-DD"
    )

    location: Optional[str] = Field(
        None, description="Локація або координати (опційно)"
    )

    description: Optional[str] = Field(
        None, description="Опис маршруту / дня походу"
    )

    filename: Optional[str] = Field(
        None,
        description="Назва .ics файлу (за замовчуванням генерується автоматично)"
    )
