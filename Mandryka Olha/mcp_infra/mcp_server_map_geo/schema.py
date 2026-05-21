from pydantic import BaseModel
from typing import List, Literal, Optional


class GeoCoordinateRequest(BaseModel):
    query: str
    lang: Optional[str] = "uk"
    limit: Optional[int] = 5
    type: Optional[List[str]] = None
    locality: Optional[List[str]] = None
    preferBBox: Optional[List[float]] = None          
    preferNear: Optional[List[float]] = None          
    preferNearPosition: Optional[float] = None  

class ReverseGeocodeRequest(BaseModel):
    lat: float
    lon: float
    lang: Optional[str] = "uk"
    limit: Optional[int] = 5
    radius: Optional[int] = 800                       
    type: Optional[List[Literal["poi", "natural", "peak", "summit", "valley"]]] = None


    