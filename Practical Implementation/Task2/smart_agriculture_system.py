import random
import time
from datetime import datetime, timedelta
from typing import List, Dict
from agriculture_types import SensorData, CropData, SystemAlert
from ai_models import CropYieldPredictor
import streamlit as st

class SmartAgricultureSystem:
    def __init__(self):
        self.sensors: List[SensorData] = []
        self.crops: List[CropData] = []
        self.alerts: List[SystemAlert] = []
        self.learning_data: List[List[float]] = []
        self.irrigation_schedule: Dict[str, bool] = {}
        self.predictor = None  # Will be set in main.py or streamlit_app.py
        self.initialize_sensors()
        self.initialize_crops()
        print("Smart Agriculture System initialized successfully!")
        print(f"Monitoring {len(self.sensors)} sensors and {len(self.crops)} crops")

    def initialize_sensors(self) -> None:
        sensor_configs = [
            {'id': 'soil_moisture', 'name': 'Soil Moisture', 'unit': '%', 'optimal_range': (20.0, 40.0)},
            {'id': 'soil_ph', 'name': 'Soil pH', 'unit': 'pH', 'optimal_range': (5.5, 7.5)},
            {'id': 'temperature', 'name': 'Temperature', 'unit': '°C', 'optimal_range': (15.0, 30.0)},
            {'id': 'rainfall', 'name': 'Rainfall', 'unit': 'mm', 'optimal_range': (100.0, 200.0)},
            {'id': 'humidity', 'name': 'Humidity', 'unit': '%', 'optimal_range': (50.0, 80.0)},
            {'id': 'sunlight_hours', 'name': 'Sunlight Hours', 'unit': 'hours', 'optimal_range': (5.0, 8.0)},
            {'id': 'NDVI_index', 'name': 'NDVI Index', 'unit': '', 'optimal_range': (0.3, 0.8)}
        ]
        for config in sensor_configs:
            sensor = SensorData(
                id=config['id'],
                name=config['name'],
                value=0.0,
                unit=config['unit'],
                optimal_range=config['optimal_range'],
                last_updated=datetime.now(),
                status='optimal'
            )
            self.sensors.append(sensor)

    def initialize_crops(self) -> None:
        now = datetime.now()
        crops_data = [
            {'crop_type': 'Wheat', 'planted_date': now - timedelta(days=30), 'expected_harvest': now + timedelta(days=90), 'health_score': 85.0, 'growth_stage': 'Flowering', 'health_status': 'None'},
            {'crop_type': 'Soybean', 'planted_date': now - timedelta(days=20), 'expected_harvest': now + timedelta(days=25), 'health_score': 92.0, 'growth_stage': 'Maturation', 'health_status': 'Mild'},
            {'crop_type': 'Maize', 'planted_date': now - timedelta(days=45), 'expected_harvest': now + timedelta(days=60), 'health_score': 78.0, 'growth_stage': 'Vegetative', 'health_status': 'Moderate'}
        ]
        for crop_data in crops_data:
            crop = CropData(
                crop_type=crop_data['crop_type'],
                planted_date=crop_data['planted_date'],
                expected_harvest=crop_data['expected_harvest'],
                predicted_yield=0.0,
                health_score=crop_data['health_score'],
                growth_stage=crop_data['growth_stage'],
                health_status=crop_data['health_status']
            )
            self.crops.append(crop)

    def generate_sensor_reading(self, sensor: SensorData) -> float:
        min_val, max_val = sensor.optimal_range
        base_value = (min_val + max_val) / 2
        variation = (max_val - min_val) * 0.3
        random_factor = (random.random() - 0.5) * 2
        new_value = base_value + variation * random_factor
        time_factor = random.uniform(0.9, 1.1)
        return round(new_value * time_factor, 2)

    def update_sensor_status(self, sensor: SensorData) -> None:
        min_val, max_val = sensor.optimal_range
        value = sensor.value
        if value < min_val * 0.8 or value > max_val * 1.2:
            sensor.status = 'critical'
        elif value < min_val * 0.9 or value > max_val * 1.1:
            sensor.status = 'warning'
        else:
            sensor.status = 'optimal'

    def learn_from_data(self, sensor_data: List[float]) -> None:
        self.learning_data.append(sensor_data.copy())
        if len(self.learning_data) > 100:
            self.learning_data.pop(0)
        if len(self.learning_data) >= 10:
            self.analyze_patterns()

    def analyze_patterns(self) -> None:
        recent_data = self.learning_data[-10:]
        for i, sensor in enumerate(self.sensors):
            if i < len(recent_data[0]):
                values = [reading[i] for reading in recent_data]
                avg_value = sum(values) / len(values)
                trend = "stable"
                if len(values) > 1:
                    if values[-1] > values[0] * 1.1:
                        trend = "increasing"
                    elif values[-1] < values[0] * 0.9:
                        trend = "decreasing"
                if trend != "stable" and sensor.status == "warning":
                    self.create_predictive_alert(sensor, trend)

    def create_predictive_alert(self, sensor: SensorData, trend: str) -> None:
        alert_id = f"predictive_{sensor.id}_{int(time.time())}"
        existing_alert = any(
            alert.message.startswith(f"Predictive: {sensor.name}") and not alert.resolved
            for alert in self.alerts
        )
        if not existing_alert:
            message = f"Predictive: {sensor.name} showing {trend} trend - may need attention soon"
            alert = SystemAlert(
                id=alert_id,
                type='warning',
                message=message,
                timestamp=datetime.now(),
                resolved=False
            )
            self.alerts.append(alert)

    def predict_crop_yield(self, crop: CropData) -> float:
        if self.predictor and self.predictor.is_trained:
            return self.predictor.predict_yield(crop, self.sensors)
        else:
            sensor_values = {sensor.id: sensor.value for sensor in self.sensors}
            health_factor = crop.health_score / 100.0
            weights = {
                'soil_moisture': 0.4,
                'soil_ph': 0.2,
                'temperature': 0.3,
                'sunlight_hours': 0.1
            }
            normalized_scores = {}
            for sensor_id, weight in weights.items():
                sensor = next((s for s in self.sensors if s.id == sensor_id), None)
                if sensor:
                    min_val, max_val = sensor.optimal_range
                    current_val = sensor_values.get(sensor_id, min_val)
                    if min_val <= current_val <= max_val:
                        normalized_scores[sensor_id] = 1.0
                    else:
                        normalized_scores[sensor_id] = max(0, current_val / min_val if current_val < min_val else max_val / current_val)
            yield_score = sum(normalized_scores.get(sensor_id, 0.5) * weight for sensor_id, weight in weights.items()) * health_factor
            base_yields = {'Wheat': 4000.0, 'Soybean': 4500.0, 'Maize': 5000.0}
            base_yield = base_yields.get(crop.crop_type, 4000.0)
            return round(base_yield * yield_score, 2)

    def check_for_alerts(self) -> None:
        for sensor in self.sensors:
            if sensor.status == 'critical':
                alert_id = f"critical_{sensor.id}_{int(time.time())}"
                existing_alert = any(
                    sensor.name in alert.message and alert.type == 'error' and not alert.resolved
                    for alert in self.alerts
                )
                if not existing_alert:
                    alert = SystemAlert(
                        id=alert_id,
                        type='error',
                        message=f"{sensor.name} is at critical level: {sensor.value}{sensor.unit}",
                        timestamp=datetime.now(),
                        resolved=False
                    )
                    self.alerts.append(alert)

    def auto_irrigate(self) -> None:
        soil_moisture_sensor = next((s for s in self.sensors if s.id == 'soil_moisture'), None)
        if soil_moisture_sensor and soil_moisture_sensor.value < 30:
            self.irrigation_schedule['field_1'] = True
            alert = SystemAlert(
                id=f"irrigation_{int(time.time())}",
                type='info',
                message=f"Automatic irrigation activated - Soil moisture: {soil_moisture_sensor.value}%",
                timestamp=datetime.now(),
                resolved=False
            )
            self.alerts.append(alert)
            print(f"🚿 AUTO-IRRIGATION: Activated due to low soil moisture ({soil_moisture_sensor.value}%)")

    def update_system(self) -> None:
        print("\n" + "="*60)
        print("📊 SYSTEM UPDATE CYCLE")
        print("="*60)
        current_readings = []
        for sensor in self.sensors:
            sensor.value = self.generate_sensor_reading(sensor)
            sensor.last_updated = datetime.now()
            self.update_sensor_status(sensor)
            current_readings.append(sensor.value)
            status_emoji = "✅" if sensor.status == "optimal" else "⚠️" if sensor.status == "warning" else "🚨"
            print(f"{status_emoji} {sensor.name}: {sensor.value}{sensor.unit} ({sensor.status})")
        
        self.learn_from_data(current_readings)
        print("\n🌱 CROP YIELD PREDICTIONS:")
        if 'historical_data' not in st.session_state:
            st.session_state.historical_data = []
        for crop in self.crops:
            crop.predicted_yield = self.predict_crop_yield(crop)
            days_to_harvest = (crop.expected_harvest - datetime.now()).days
            print(f"   {crop.crop_type}: {crop.predicted_yield}kg/ha (harvest in {days_to_harvest} days)")
            st.session_state.historical_data.append({
                'plot': f"{crop.crop_type} ({crop.growth_stage})",
                'yield': crop.predicted_yield
            })
        
        self.check_for_alerts()
        self.auto_irrigate()
        self.display_system_status()

    def display_system_status(self) -> None:
        critical_sensors = sum(1 for s in self.sensors if s.status == 'critical')
        warning_sensors = sum(1 for s in self.sensors if s.status == 'warning')
        active_alerts = sum(1 for a in self.alerts if not a.resolved)
        status = "🚨 CRITICAL" if critical_sensors > 0 else "⚠️ WARNING" if warning_sensors > 0 else "✅ OPTIMAL"
        print(f"\n🏭 SYSTEM STATUS: {status}")
        print(f"📡 Active Sensors: {len(self.sensors) - critical_sensors}/{len(self.sensors)}")
        print(f"🚨 Active Alerts: {active_alerts}")
        print(f"💧 Irrigation Active: {'Yes' if self.irrigation_schedule.get('field_1', False) else 'No'}")

    def get_sensor_data(self) -> List[SensorData]:
        return self.sensors.copy()

    def get_crop_data(self) -> List[CropData]:
        return self.crops.copy()

    def get_alerts(self) -> List[SystemAlert]:
        return [alert for alert in self.alerts if not alert.resolved]

    def get_system_status(self) -> str:
        critical_sensors = sum(1 for s in self.sensors if s.status == 'critical')
        warning_sensors = sum(1 for s in self.sensors if s.status == 'warning')
        return 'Critical' if critical_sensors > 0 else 'Warning' if warning_sensors > 0 else 'Optimal'

    def resolve_alert(self, alert_id: str) -> bool:
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.resolved = True
                print(f"✅ Alert resolved: {alert.message}")
                return True
        return False

    def get_historical_data(self) -> List[List[float]]:
        return self.learning_data.copy()

    def generate_report(self) -> Dict:
        return {
            'timestamp': datetime.now(),
            'system_status': self.get_system_status(),
            'sensors': len(self.sensors),
            'crops': len(self.crops),
            'active_alerts': len(self.get_alerts()),
            'sensor_data': [
                {'name': s.name, 'value': s.value, 'unit': s.unit, 'status': s.status}
                for s in self.sensors
            ],
            'crop_predictions': [
                {'type': c.crop_type, 'predicted_yield': c.predicted_yield, 'health_score': c.health_score, 'growth_stage': c.growth_stage}
                for c in self.crops
            ]
        }