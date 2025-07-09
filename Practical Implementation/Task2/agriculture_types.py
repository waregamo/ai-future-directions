from datetime import datetime
from typing import List, Tuple, Dict, Any
from dataclasses import dataclass

@dataclass
class SensorData:
    id: str
    name: str
    value: float
    unit: str
    optimal_range: Tuple[float, float]
    last_updated: datetime
    status: str

@dataclass
class CropData:
    crop_type: str
    planted_date: datetime
    expected_harvest: datetime
    predicted_yield: float
    health_score: float
    growth_stage: str
    health_status: str = 'None'

@dataclass
class SystemAlert:
    id: str
    type: str
    message: str
    timestamp: datetime
    resolved: bool

@dataclass
class WeatherData:
    temperature: float
    humidity: float
    pressure: float
    wind_speed: float
    forecast: str