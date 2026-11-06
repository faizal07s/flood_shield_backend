import random
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# 1. Database Configuration (SQLite Setup)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///floodshield.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 2. Database Model (Table Structure for Weather/Flood Logs)
class FloodLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    rainfall_mm = db.Column(db.Float, nullable=False)
    water_level_m = db.Column(db.Float, nullable=False)
    temperature_c = db.Column(db.Float, nullable=False)
    humidity_percent = db.Column(db.Integer, nullable=False)
    risk_level = db.Column(db.String(50), nullable=False)
    alert_message = db.Column(db.String(200), nullable=False)

# Create database tables automatically inside app context
with app.app_context():
    db.create_all()

# Home Route
@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "message": "Welcome to FloodShield Backend API",
        "available_endpoints": [
            "/api/weather (GET - Fetches live simulated data & saves to DB)",
            "/api/history (GET - Fetches past alert logs from DB)"
        ]
    })

# 3. Live Weather/Flood Simulation & Save Endpoint
@app.route('/api/weather', methods=['GET'])
def get_weather_data():
    rainfall = round(random.uniform(5.0, 150.0), 2)
    water_level = round(random.uniform(0.5, 6.0), 2)
    temperature = round(random.uniform(22.0, 38.0), 1)
    humidity = random.randint(50, 95)

    if rainfall > 80.0 or water_level > 4.5:
        risk_level = "CRITICAL"
        alert_message = "HIGH FLOOD RISK! Evacuate to safe areas immediately."
        status_code = "RED_ALERT"
    elif rainfall > 40.0 or water_level > 3.0:
        risk_level = "MODERATE"
        alert_message = "Heavy rainfall detected. Stay updated with alerts."
        status_code = "YELLOW_ALERT"
    else:
        risk_level = "LOW"
        alert_message = "Weather condition normal. No immediate threat."
        status_code = "GREEN_NORMAL"

    new_log = FloodLog(
        rainfall_mm=rainfall,
        water_level_m=water_level,
        temperature_c=temperature,
        humidity_percent=humidity,
        risk_level=risk_level,
        alert_message=alert_message
    )
    db.session.add(new_log)
    db.session.commit()

    return jsonify({
        "status": "success",
        "log_id": new_log.id,
        "location": "Surat Region Zone-A",
        "sensor_data": {
            "rainfall_mm": rainfall,
            "water_level_m": water_level,
            "temperature_c": temperature,
            "humidity_percent": humidity
        },
        "flood_analysis": {
            "risk_level": risk_level,
            "alert_message": alert_message,
            "status_code": status_code
        }
    })

# 4. History Logs Endpoint (Fetches recent records from database)
@app.route('/api/history', methods=['GET'])
def get_weather_history():
    # Fetch last 10 logs from database, newest first
    logs = FloodLog.query.order_by(FloodLog.timestamp.desc()).limit(10).all()
    
    history_list = []
    for log in logs:
        history_list.append({
            "log_id": log.id,
            "timestamp": log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            "rainfall_mm": log.rainfall_mm,
            "water_level_m": log.water_level_m,
            "risk_level": log.risk_level,
            "alert_message": log.alert_message
        })

    return jsonify({
        "status": "success",
        "count": len(history_list),
        "history": history_list
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)