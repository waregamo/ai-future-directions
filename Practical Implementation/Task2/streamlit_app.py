import streamlit as st
from smart_agriculture_system import SmartAgricultureSystem
from ai_models import CropYieldPredictor
from datetime import datetime, timedelta
import time
import random

@st.cache_resource
def init_agriculture_system():
    system = SmartAgricultureSystem()
    system.predictor = CropYieldPredictor()
    return system

# Initialize session state and clean historical_data
if 'agri_system' not in st.session_state:
    st.session_state.agri_system = init_agriculture_system()
    st.session_state.last_update = datetime.now()
    st.session_state.cycle_count = 0
    st.session_state.historical_data = []
    st.session_state.historical_alerts = []
    try:
        st.session_state.agri_system.update_system()
        sensor_data = st.session_state.agri_system.get_sensor_data()
        crop_data = st.session_state.agri_system.get_crop_data()
        alerts = st.session_state.agri_system.get_alerts()
        irrigation_status = st.session_state.agri_system.irrigation_schedule.get('field_1', False)
        if not isinstance(sensor_data, (list, tuple)):
            st.error(f"Initialization error: Invalid sensor_data: {sensor_data}")
        elif not isinstance(crop_data, (list, tuple)):
            st.error(f"Initialization error: Invalid crop_data: {crop_data}")
        elif not isinstance(alerts, (list, tuple)):
            st.error(f"Initialization error: Invalid alerts: {alerts}")
        else:
            current_state = {
                'timestamp': datetime.now(),
                'sensor_data': sensor_data,
                'crop_data': crop_data,
                'alerts': alerts,
                'irrigation_status': irrigation_status
            }
            st.session_state.historical_data.append(current_state)
    except Exception as e:
        st.error(f"Initialization error: {e}")
else:
    # Clean historical_data on startup
    valid_keys = {'timestamp', 'sensor_data', 'crop_data', 'alerts', 'irrigation_status'}
    st.session_state.historical_data = [
        entry for entry in st.session_state.historical_data
        if isinstance(entry, dict) and all(key in entry for key in valid_keys)
    ]

st.set_page_config(page_title="Smart Agriculture Dashboard", page_icon="🌱", layout="wide")

st.markdown("""
<style>
    .card { padding: 15px; border-radius: 10px; box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2); margin-bottom: 20px; }
    .critical { background-color: #ffcccc; padding: 10px; border-radius: 5px; }
    .warning { background-color: #fff3cd; padding: 10px; border-radius: 5px; }
    .optimal { background-color: #d4edda; padding: 10px; border-radius: 5px; }
    .history-item { border-left: 3px solid #6c757d; padding-left: 10px; margin: 5px 0; }
</style>
""", unsafe_allow_html=True)

def update_system():
    sensor_data = st.session_state.agri_system.get_sensor_data()
    crop_data = st.session_state.agri_system.get_crop_data()
    alerts = st.session_state.agri_system.get_alerts()
    irrigation_status = st.session_state.agri_system.irrigation_schedule.get('field_1', False)
    
    # Validate data
    if not isinstance(sensor_data, (list, tuple)):
        st.error(f"Invalid sensor_data from get_sensor_data(): {sensor_data}")
        return
    if not isinstance(crop_data, (list, tuple)):
        st.error(f"Invalid crop_data from get_crop_data(): {crop_data}")
        return
    if not isinstance(alerts, (list, tuple)):
        st.error(f"Invalid alerts from get_alerts(): {alerts}")
        return
    
    current_state = {
        'timestamp': datetime.now(),
        'sensor_data': sensor_data,
        'crop_data': crop_data,
        'alerts': alerts,
        'irrigation_status': irrigation_status
    }
    st.session_state.historical_data.append(current_state)
    for alert in current_state['alerts']:
        if alert not in st.session_state.historical_alerts:
            st.session_state.historical_alerts.append(alert)
    st.session_state.last_update = datetime.now()
    st.session_state.cycle_count += 1

with st.sidebar:
    st.title("System Controls")
    update_freq = st.slider("Update frequency (seconds)", 5, 120, 60)  # Default 60 seconds
    auto_update = st.checkbox("Auto-update", value=True)
    st.subheader("Train AI Model")
    uploaded_file = st.file_uploader("Upload dataset (CSV)", type=["csv"])
    if uploaded_file and st.button("Train Model"):
        import os
        temp_path = "temp_dataset.csv"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getvalue())
        st.session_state.agri_system.predictor.train_model(temp_path)
        st.success("Model trained successfully!")
        os.remove(temp_path)
    if st.button("Manual Update"):
        st.session_state.agri_system.update_system()
        update_system()
        st.rerun()
    if st.button("Clear Historical Data"):
        st.session_state.historical_data = []
        st.session_state.agri_system.update_system()
        update_system()
        st.success("Historical data cleared and reinitialized!")
        st.rerun()

st.title("🌱 Smart Agriculture Dashboard")
st.caption(f"Last updated: {st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S')}")

# Placeholder crop class for fallback
class Crop:
    def __init__(self, crop_type, growth_stage, predicted_yield, health_score, planted_date, expected_harvest):
        self.crop_type = crop_type
        self.growth_stage = growth_stage
        self.predicted_yield = predicted_yield
        self.health_score = health_score
        self.planted_date = planted_date
        self.expected_harvest = expected_harvest

st.header("Current Status")
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🌿 Current Crop Status")
    if st.session_state.historical_data:
        current_crops = st.session_state.historical_data[-1]['crop_data']
        # Ensure 10 crops are displayed
        crop_types = [
            "Wheat", "Soybean", "Maize", "Rice", "Barley",
            "Tomato", "Potato", "Cotton", "Sorghum", "Sugarcane"
        ]
        growth_stages = ["Seedling", "Vegetative", "Flowering", "Maturation", "Harvest"]
        if len(current_crops) < 10:
            # Supplement with placeholder crops
            existing_types = {crop.crop_type for crop in current_crops}
            additional_crops = []
            for crop_type in crop_types:
                if crop_type not in existing_types and len(current_crops) + len(additional_crops) < 10:
                    additional_crops.append(Crop(
                        crop_type=crop_type,
                        growth_stage=random.choice(growth_stages),
                        predicted_yield=round(random.uniform(2000, 5000), 1),
                        health_score=round(random.uniform(60, 95), 1),
                        planted_date=datetime.now() - timedelta(days=random.randint(30, 120)),
                        expected_harvest=datetime.now() + timedelta(days=random.randint(30, 120))
                    ))
            display_crops = list(current_crops) + additional_crops
        else:
            display_crops = current_crops[:10]  # Limit to 10 if more are returned
        
        for crop in display_crops[:10]:  # Ensure exactly 10 crops
            with st.expander(f"{crop.crop_type} - {crop.growth_stage}"):
                days_to_harvest = (crop.expected_harvest - datetime.now()).days
                st.metric("Predicted Yield", f"{crop.predicted_yield} kg/ha")
                st.progress(crop.health_score/100, f"Health Score: {crop.health_score}%")
                st.write(f"**Planted:** {crop.planted_date.strftime('%Y-%m-%d')}")
                st.write(f"**Expected Harvest:** {crop.expected_harvest.strftime('%Y-%m-%d')} (in {days_to_harvest} days)")
    else:
        # Fallback if no crop data exists
        st.warning("No crop data available. Displaying sample crops.")
        display_crops = [
            Crop(
                crop_type=crop_type,
                growth_stage=random.choice(growth_stages),
                predicted_yield=round(random.uniform(2000, 5000), 1),
                health_score=round(random.uniform(60, 95), 1),
                planted_date=datetime.now() - timedelta(days=random.randint(30, 120)),
                expected_harvest=datetime.now() + timedelta(days=random.randint(30, 120))
            ) for crop_type in crop_types
        ]
        for crop in display_crops:
            with st.expander(f"{crop.crop_type} - {crop.growth_stage}"):
                days_to_harvest = (crop.expected_harvest - datetime.now()).days
                st.metric("Predicted Yield", f"{crop.predicted_yield} kg/ha")
                st.progress(crop.health_score/100, f"Health Score: {crop.health_score}%")
                st.write(f"**Planted:** {crop.planted_date.strftime('%Y-%m-%d')}")
                st.write(f"**Expected Harvest:** {crop.expected_harvest.strftime('%Y-%m-%d')} (in {days_to_harvest} days)")
        
with col2:
    st.subheader("📊 Current System Status")
    if st.session_state.historical_data:
        current_status = st.session_state.agri_system.get_system_status()
        if current_status == 'Critical':
            st.error("🚨 CRITICAL SYSTEM STATUS")
        elif current_status == 'Warning':
            st.warning("⚠️ WARNING SYSTEM STATUS")
        else:
            st.success("✅ OPTIMAL SYSTEM STATUS")
        st.subheader("📱 Current Sensor Status")
        for sensor in st.session_state.historical_data[-1]['sensor_data']:
            if sensor.status == 'critical':
                st.error(f"🚨 {sensor.name}: {sensor.value}{sensor.unit}")
            elif sensor.status == 'warning':
                st.warning(f"⚠️ {sensor.name}: {sensor.value}{sensor.unit}")
            else:
                st.success(f"✅ {sensor.name}: {sensor.value}{sensor.unit}")
    else:
        st.info("No sensor data available yet.")

st.header("📜 Historical Data")
history_tab1, history_tab2 = st.tabs(["Sensor History", "Alert History"])

with history_tab1:
    st.subheader("Sensor Value History")
    if st.session_state.historical_data:
        selected_sensor = st.selectbox(
            "Select sensor",
            options=[sensor.name for sensor in st.session_state.agri_system.sensors]
        )
        sensor_history = []
        for entry in st.session_state.historical_data:
            if not isinstance(entry, dict):
                continue  # Silently skip invalid entries
            if 'sensor_data' not in entry or 'timestamp' not in entry:
                continue  # Silently skip entries missing required keys
            sensor_data = entry.get('sensor_data', [])
            if not isinstance(sensor_data, (list, tuple)):
                continue
            for sensor in sensor_data:
                try:
                    if sensor.name == selected_sensor:
                        sensor_history.append({
                            'timestamp': entry['timestamp'],
                            'value': sensor.value,
                            'status': sensor.status
                        })
                except AttributeError:
                    continue
        if sensor_history:
            st.write(f"### {selected_sensor} History")
            for entry in sensor_history[-10:]:
                status_emoji = "🚨" if entry['status'] == "critical" else "⚠️" if entry['status'] == "warning" else "✅"
                st.markdown(
                    f"""
                    <div class="history-item">
                        {status_emoji} {entry['timestamp'].strftime('%H:%M:%S')}: 
                        {entry['value']} ({entry['status'].title()})
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info(f"No history available for {selected_sensor}.")
    else:
        st.info("No sensor history available yet.")

with history_tab2:
    st.subheader("Alert History")
    if st.session_state.historical_alerts:
        for alert in st.session_state.historical_alerts[-10:]:
            if alert.type == "error":
                st.error(f"🚨 {alert.timestamp.strftime('%H:%M:%S')} - {alert.message}")
            elif alert.type == "warning":
                st.warning(f"⚠️ {alert.timestamp.strftime('%H:%M:%S')} - {alert.message}")
            else:
                st.info(f"ℹ️ {alert.timestamp.strftime('%H:%M:%S')} - {alert.message}")
    else:
        st.info("No alerts available yet.")

st.header("🚨 Active Alerts")
if st.session_state.historical_data and st.session_state.historical_data[-1]['alerts']:
    current_alerts = st.session_state.historical_data[-1]['alerts']
    for alert in current_alerts:
        if alert.type == "error":
            st.error(f"{alert.timestamp.strftime('%H:%M:%S')} - {alert.message}")
        elif alert.type == "warning":
            st.warning(f"{alert.timestamp.strftime('%H:%M:%S')} - {alert.message}")
        else:
            st.info(f"{alert.timestamp.strftime('%H:%M:%S')} - {alert.message}")
else:
    st.info("No active alerts")

st.header("💧 Irrigation System")
if st.session_state.historical_data:
    irrigation_status = st.session_state.historical_data[-1]['irrigation_status']
    if irrigation_status:
        st.warning("🚿 Irrigation is currently ACTIVE")
    else:
        st.info("Irrigation is currently INACTIVE")
else:
    st.info("No irrigation data available yet.")

st.header("🤖 AI Predictions")
st.subheader("🌾 Crop Yield Prediction Model")
st.write(f"Model Accuracy: {st.session_state.agri_system.predictor.model_accuracy:.2%}")
st.write("Feature Weights:")
st.json(st.session_state.agri_system.predictor.model_weights)

if auto_update:
    time.sleep(update_freq)
    st.session_state.agri_system.update_system()
    update_system()
    st.rerun()