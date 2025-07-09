import random
import time
from datetime import datetime
from typing import Dict, List
from agriculture_types import SensorData

class IoTSensorSimulator:
    """Simulates various IoT sensors used in smart agriculture"""
    
    def __init__(self):
        self.sensors_config = {
            'soil_moisture': {
                'name': 'Soil Moisture Sensor',
                'unit': '%',
                'range': (0, 100),
                'optimal': (40, 70),
                'drift_rate': 0.1
            },
            'soil_temperature': {
                'name': 'Soil Temperature Sensor',
                'unit': '°C',
                'range': (5, 40),
                'optimal': (18, 25),
                'drift_rate': 0.05
            },
            'air_humidity': {
                'name': 'Air Humidity Sensor',
                'unit': '%',
                'range': (20, 100),
                'optimal': (50, 80),
                'drift_rate': 0.08
            },
            'soil_ph': {
                'name': 'Soil pH Sensor',
                'unit': 'pH',
                'range': (4.0, 9.0),
                'optimal': (6.0, 7.5),
                'drift_rate': 0.02
            },
            'light_intensity': {
                'name': 'Light Intensity Sensor',
                'unit': 'lux',
                'range': (0, 100000),
                'optimal': (10000, 50000),
                'drift_rate': 0.15
            },
            'nitrogen_level': {
                'name': 'Nitrogen Level Sensor',
                'unit': 'ppm',
                'range': (0, 100),
                'optimal': (20, 50),
                'drift_rate': 0.03
            }
        }
        
        self.sensor_states = {}
        self.initialize_sensors()
    
    def initialize_sensors(self):
        """Initialize sensor states with random starting values"""
        for sensor_id, config in self.sensors_config.items():
            optimal_min, optimal_max = config['optimal']
            # Start sensors near optimal values
            initial_value = random.uniform(optimal_min, optimal_max)
            
            self.sensor_states[sensor_id] = {
                'current_value': initial_value,
                'last_reading': datetime.now(),
                'drift_direction': random.choice([-1, 1]),
                'noise_level': random.uniform(0.01, 0.05)
            }
    
    def simulate_environmental_factors(self) -> Dict[str, float]:
        """Simulate environmental factors that affect sensor readings"""
        current_hour = datetime.now().hour
        
        # Time-based factors
        time_factors = {
            'temperature_factor': 1.0 + 0.3 * abs(12 - current_hour) / 12,  # Cooler at night
            'light_factor': max(0.1, 1.0 - abs(12 - current_hour) / 12),    # Dark at night
            'humidity_factor': 1.0 + 0.2 * (abs(12 - current_hour) / 12),   # Higher at night
        }
        
        # Weather simulation
        weather_conditions = random.choice(['sunny', 'cloudy', 'rainy', 'windy'])
        weather_factors = {
            'sunny': {'temp': 1.2, 'humidity': 0.8, 'light': 1.3},
            'cloudy': {'temp': 0.9, 'humidity': 1.1, 'light': 0.6},
            'rainy': {'temp': 0.8, 'humidity': 1.4, 'light': 0.4},
            'windy': {'temp': 0.9, 'humidity': 0.9, 'light': 1.0}
        }
        
        return {
            'time_factors': time_factors,
            'weather': weather_conditions,
            'weather_factors': weather_factors[weather_conditions]
        }
    
    def read_sensor(self, sensor_id: str) -> float:
        """Simulate reading from a specific sensor"""
        if sensor_id not in self.sensors_config:
            raise ValueError(f"Unknown sensor: {sensor_id}")
        
        config = self.sensors_config[sensor_id]
        state = self.sensor_states[sensor_id]
        env_factors = self.simulate_environmental_factors()
        
        # Base value with drift
        current_value = state['current_value']
        drift_rate = config['drift_rate']
        
        # Apply environmental factors
        if sensor_id == 'soil_temperature':
            current_value *= env_factors['time_factors']['temperature_factor']
            current_value *= env_factors['weather_factors']['temp']
        elif sensor_id == 'air_humidity':
            current_value *= env_factors['time_factors']['humidity_factor']
            current_value *= env_factors['weather_factors']['humidity']
        elif sensor_id == 'light_intensity':
            current_value *= env_factors['time_factors']['light_factor']
            current_value *= env_factors['weather_factors']['light']
        elif sensor_id == 'soil_moisture' and env_factors['weather'] == 'rainy':
            current_value *= 1.3  # Increase moisture during rain
        
        # Add sensor drift
        drift = random.uniform(-drift_rate, drift_rate) * state['drift_direction']
        current_value += drift
        
        # Add noise
        noise = random.uniform(-state['noise_level'], state['noise_level']) * current_value
        current_value += noise
        
        # Ensure value stays within sensor range
        min_val, max_val = config['range']
        current_value = max(min_val, min(max_val, current_value))
        
        # Update sensor state
        state['current_value'] = current_value
        state['last_reading'] = datetime.now()
        
        # Occasionally change drift direction
        if random.random() < 0.1:
            state['drift_direction'] *= -1
        
        return round(current_value, 2)
    
    def read_all_sensors(self) -> Dict[str, float]:
        """Read all sensors and return their values"""
        readings = {}
        for sensor_id in self.sensors_config.keys():
            readings[sensor_id] = self.read_sensor(sensor_id)
        return readings
    
    def simulate_sensor_failure(self, sensor_id: str, duration: int = 30):
        """Simulate sensor failure for testing"""
        if sensor_id in self.sensor_states:
            print(f"⚠️ Simulating {sensor_id} failure for {duration} seconds")
            # Set sensor to extreme value to trigger alerts
            config = self.sensors_config[sensor_id]
            min_val, max_val = config['range']
            self.sensor_states[sensor_id]['current_value'] = random.choice([min_val, max_val])
            
            # Schedule recovery (in a real system, this would be handled differently)
            time.sleep(duration)
            optimal_min, optimal_max = config['optimal']
            self.sensor_states[sensor_id]['current_value'] = random.uniform(optimal_min, optimal_max)
            print(f"✅ {sensor_id} recovered")

def test_sensor_simulator():
    """Test the sensor simulator"""
    print("🧪 Testing IoT Sensor Simulator")
    print("=" * 30)
    
    simulator = IoTSensorSimulator()
    
    # Test individual sensor readings
    for i in range(5):
        print(f"\nReading Set {i+1}:")
        readings = simulator.read_all_sensors()
        
        for sensor_id, value in readings.items():
            config = simulator.sensors_config[sensor_id]
            unit = config['unit']
            optimal_min, optimal_max = config['optimal']
            
            status = "✅" if optimal_min <= value <= optimal_max else "⚠️"
            print(f"  {status} {config['name']}: {value}{unit}")
        
        time.sleep(2)
    
    print("\n✅ Sensor simulator test completed!")

if __name__ == "__main__":
    test_sensor_simulator()