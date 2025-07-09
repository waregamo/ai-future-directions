from typing import Tuple

class SensorData:
    def __init__(self, id: str, value: float, optimal_range: Tuple[float, float]):
        self.id = id
        self.value = value
        self.optimal_range = optimal_range

class CropData:
    def __init__(self, crop_type: str, health_score: float, growth_stage: str, health_status: str = 'None'):
        self.crop_type = crop_type
        self.health_score = health_score
        self.growth_stage = growth_stage
        self.health_status = health_status
