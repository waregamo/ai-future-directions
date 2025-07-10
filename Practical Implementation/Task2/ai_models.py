import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from typing import List, Dict, Tuple, Any
from agriculture_types import SensorData, CropData
import random

class CropYieldPredictor:
    def __init__(self):
        self.model_weights = {
            'soil_moisture': 0.35,
            'soil_pH': 0.20,
            'temperature': 0.25,
            'rainfall': 0.10,
            'humidity': 0.05,
            'sunlight_hours': 0.03,
            'NDVI_index': 0.02
        }
        self.crop_coefficients = {
            'Wheat': {'base_yield': 4000.0, 'temp_sensitivity': 1.0, 'water_need': 1.1},
            'Soybean': {'base_yield': 4500.0, 'temp_sensitivity': 1.2, 'water_need': 1.0},
            'Maize': {'base_yield': 5000.0, 'temp_sensitivity': 1.3, 'water_need': 1.2},
            'Cotton': {'base_yield': 3500.0, 'temp_sensitivity': 1.1, 'water_need': 1.3},
            'Rice': {'base_yield': 4500.0, 'temp_sensitivity': 1.2, 'water_need': 1.4}
        }
        self.training_data = []
        self.model_accuracy = 0.85
        self.numerical_features = ['soil_moisture_%', 'soil_pH', 'temperature_C', 'rainfall_mm', 
                                 'humidity_%', 'sunlight_hours', 'NDVI_index']
        self.categorical_features = ['crop_type', 'crop_disease_status']
        self.preprocessor = ColumnTransformer(
            transformers=[
                ('num', StandardScaler(), self.numerical_features),
                ('cat', OneHotEncoder(drop='first', sparse_output=False, handle_unknown='ignore'), 
                 self.categorical_features)
            ])
        self.model = Pipeline([
            ('preprocessor', self.preprocessor),
            ('regressor', RandomForestRegressor(n_estimators=100, random_state=42))
        ])
        self.is_trained = False

    def train_model(self, dataset_path: str):
        """Train the model using a CSV dataset."""
        try:
            df = pd.read_csv(dataset_path)
            features = self.numerical_features + self.categorical_features
            target = 'yield_kg_per_hectare'
            df = df.dropna(subset=features + [target])
            X = df[features]
            y = df[target]
            self.model.fit(X, y)
            self.is_trained = True
            self.model_accuracy = self.model.score(X, y)
            feature_names = (self.numerical_features + 
                           list(self.model.named_steps['preprocessor']
                                .named_transformers_['cat']
                                .get_feature_names_out(self.categorical_features)))
            importances = self.model.named_steps['regressor'].feature_importances_
            for feature, importance in zip(feature_names, importances):
                for key in self.model_weights:
                    if key in feature:
                        self.model_weights[key] = importance
            print(f"🤖 Model trained with {len(df)} data points")
            print(f"📊 Model accuracy (R²): {self.model_accuracy:.2%}")
            self.training_data = df.to_dict('records')
        except Exception as e:
            print(f"❌ Error training model: {str(e)}")

    def predict_yield(self, crop: CropData, sensors: List[SensorData]) -> float:
        """Predict crop yield using the trained model or fallback to heuristic logic."""
        if self.is_trained:
            sensor_dict = {sensor.id: sensor.value for sensor in sensors}
            input_data = {
                'soil_moisture_%': sensor_dict.get('soil_moisture', 30.0),
                'soil_pH': sensor_dict.get('soil_pH', 6.5),
                'temperature_C': sensor_dict.get('temperature', 25.0),
                'rainfall_mm': sensor_dict.get('rainfall', 150.0),
                'humidity_%': sensor_dict.get('humidity', 60.0),
                'sunlight_hours': sensor_dict.get('sunlight_hours', 6.0),
                'NDVI_index': sensor_dict.get('NDVI_index', 0.5),
                'crop_type': crop.crop_type,
                'crop_disease_status': crop.health_status if hasattr(crop, 'health_status') else 'None'
            }
            input_df = pd.DataFrame([input_data])
            predicted_yield = self.model.predict(input_df)[0]
            crop_coeff = self.crop_coefficients.get(crop.crop_type, {
                'base_yield': 4000.0, 'temp_sensitivity': 1.0, 'water_need': 1.0
            })
            health_factor = crop.health_score / 100.0 if hasattr(crop, 'health_score') else 1.0
            stage_factor = self.get_growth_stage_factor(crop.growth_stage)
            predicted_yield *= health_factor * stage_factor * crop_coeff['base_yield'] / 4000.0
            return round(max(0.0, predicted_yield), 2)
        else:
            sensor_dict = {sensor.id: sensor for sensor in sensors}
            environmental_score = 0.0
            for sensor_id, weight in self.model_weights.items():
                if sensor_id in sensor_dict:
                    sensor = sensor_dict[sensor_id]
                    normalized_value = self.normalize_sensor_value(sensor.value, sensor.optimal_range)
                    environmental_score += normalized_value * weight
            crop_coeff = self.crop_coefficients.get(crop.crop_type, {
                'base_yield': 4000.0, 'temp_sensitivity': 1.0, 'water_need': 1.0
            })
            if 'temperature' in sensor_dict:
                temp_sensor = sensor_dict['temperature']
                temp_factor = self.calculate_temperature_factor(
                    temp_sensor.value, temp_sensor.optimal_range, crop_coeff['temp_sensitivity']
                )
                environmental_score *= temp_factor
            if 'soil_moisture' in sensor_dict:
                moisture_sensor = sensor_dict['soil_moisture']
                water_factor = self.calculate_water_factor(
                    moisture_sensor.value, moisture_sensor.optimal_range, crop_coeff['water_need']
                )
                environmental_score *= water_factor
            health_factor = crop.health_score / 100.0 if hasattr(crop, 'health_score') else 1.0
            stage_factor = self.get_growth_stage_factor(crop.growth_stage)
            base_yield = crop_coeff['base_yield']
            predicted_yield = base_yield * environmental_score * health_factor * stage_factor
            variation = random.uniform(0.9, 1.1)
            predicted_yield *= variation
            return round(max(0.0, predicted_yield), 2)

    def normalize_sensor_value(self, value: float, optimal_range: Tuple[float, float]) -> float:
        min_optimal, max_optimal = optimal_range
        if min_optimal <= value <= max_optimal:
            return 1.0
        elif value < min_optimal:
            return max(0.0, value / min_optimal)
        else:
            return max(0.0, max_optimal / value)

    def calculate_temperature_factor(self, temp: float, optimal_range: Tuple[float, float], sensitivity: float) -> float:
        min_temp, max_temp = optimal_range
        optimal_temp = (min_temp + max_temp) / 2
        temp_deviation = abs(temp - optimal_temp) / optimal_temp
        temp_factor = 1.0 - (temp_deviation * sensitivity * 0.5)
        return max(0.1, temp_factor)

    def calculate_water_factor(self, moisture: float, optimal_range: Tuple[float, float], water_need: float) -> float:
        min_moisture, max_moisture = optimal_range
        if moisture < min_moisture:
            water_factor = (moisture / min_moisture) * water_need
        elif moisture > max_moisture:
            water_factor = 1.0 - ((moisture - max_moisture) / max_moisture) * 0.3
        else:
            water_factor = 1.0
        return max(0.1, water_factor)

    def get_growth_stage_factor(self, growth_stage: str) -> float:
        stage_factors = {
            'Seedling': 0.3,
            'Vegetative': 0.6,
            'Flowering': 0.9,
            'Fruiting': 1.0,
            'Maturation': 1.0,
            'Harvest': 1.0
        }
        return stage_factors.get(growth_stage, 0.8)