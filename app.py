from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import requests

app = Flask(__name__)

# Database Configuration (SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///floodshield.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models for Flood Reports
class IncidentReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location_name = db.Column(db.String(100), nullable=False)
    water_level = db.Column(db.String(50), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

with app.app_context():
    db.create_all()

# API Endpoints
@app.route('/')
def home():
    return jsonify({"status": "success", "message": "FloodShield Backend Server Running"})

# Open-Meteo Weather & Rainfall API Integration
@app.route('/api/weather', methods=['GET'])
def get_weather():
    lat = request.args.get('lat', 21.1702) # Default location coord
    lon = request.args.get('lon', 72.8311)
    
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,rain,showers,weather_code"
    
    response = requests.get(url)
    if response.status_code == 200:
        weather_data = response.json()
        current_rain = weather_data.get('current', {}).get('rain', 0.0)
        
        risk = "Safe"
        if current_rain > 5.0:
            risk = "High Risk - Flood Warning"
        elif current_rain > 2.0:
            risk = "Moderate Risk"
            
        return jsonify({"status": "success", "risk_level": risk, "data": weather_data})
    else:
        return jsonify({"status": "error", "message": "Failed to fetch weather data"}), 500

# Report Waterlogging / Incident Endpoint
@app.route('/api/report', methods=['POST'])
def submit_report():
    data = request.json
    new_report = IncidentReport(
        location_name=data.get('location_name'),
        water_level=data.get('water_level'),
        latitude=data.get('latitude'),
        longitude=data.get('longitude')
    )
    db.session.add(new_report)
    db.session.commit()
    return jsonify({"status": "success", "message": "Report logged successfully"}), 201

if __name__ == '__main__':
    app.run(debug=True, port=5000)