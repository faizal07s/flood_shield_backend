from datetime import datetime
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import firebase_admin
from firebase_admin import credentials, messaging

app = Flask(__name__)
CORS(app)

# Database Configuration (SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flood_shield.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 1. User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(20), default="citizen") # citizen, admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "created_at": self.created_at.isoformat()
        }

# 2. Incident Report Model
class IncidentReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(120), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), nullable=False) # Low, Moderate, High, Critical
    status = db.Column(db.String(20), default="Pending") # Pending, Resolved
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "location": self.location,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "description": self.description,
            "severity": self.severity,
            "status": self.status,
            "timestamp": self.timestamp.isoformat()
        }

# Initialize database tables
with app.app_context():
    db.create_all()

# Firebase Initialization (Mock mode fallback if JSON key is not added yet)
try:
    cred = credentials.Certificate("firebase_config.json")
    firebase_admin.initialize_app(cred)
    FIREBASE_INITIALIZED = True
except Exception as e:
    FIREBASE_INITIALIZED = False
    print("Firebase Warning: Service account key not found. Notifications will run in mock mode.")

# Home Route
@app.route('/')
def home():
    return jsonify({"message": "Welcome to FloodShield Backend API (Team TM004301)"}), 200

# Weather API Route (Open-Meteo Integration)
@app.route('/api/weather', methods=['GET'])
def get_weather():
    try:
        lat = request.args.get('lat', default=21.1702, type=float) # Default Surat coords
        lon = request.args.get('lon', default=72.8311, type=float)
        
        open_meteo_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,precipitation,rain,weather_code"
        
        response = requests.get(open_meteo_url)
        data = response.json()
        
        if response.status_code == 200:
            current_weather = data.get('current', {})
            precipitation = current_weather.get('precipitation', 0.0)
            
            risk_level = "Low"
            if precipitation > 5.0:
                risk_level = "Moderate"
            if precipitation > 20.0:
                risk_level = "High"
                
            return jsonify({
                "status": "success",
                "latitude": lat,
                "longitude": lon,
                "temperature": current_weather.get('temperature_2m'),
                "precipitation": precipitation,
                "rain": current_weather.get('rain', 0.0),
                "risk_level": risk_level
            }), 200
        else:
            return jsonify({"status": "error", "message": "Failed to fetch data from Open-Meteo"}), 500

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Reports API Route (Submit & Fetch Incidents)
@app.route('/api/reports', methods=['GET', 'POST'])
def handle_reports():
    if request.method == 'POST':
        data = request.get_json()
        try:
            new_report = IncidentReport(
                location=data.get('location'),
                latitude=data.get('latitude', 0.0),
                longitude=data.get('longitude', 0.0),
                description=data.get('description'),
                severity=data.get('severity', 'Moderate')
            )
            db.session.add(new_report)
            db.session.commit()
            return jsonify({"status": "success", "message": "Incident report submitted successfully!", "report": new_report.to_dict()}), 201
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 400

    elif request.method == 'GET':
        reports = IncidentReport.query.order_by(IncidentReport.timestamp.desc()).all()
        return jsonify({
            "status": "success",
            "count": len(reports),
            "reports": [report.to_dict() for report in reports]
        }), 200

# Notifications / Risk Alert API Route (Firebase Cloud Messaging)
@app.route('/api/send-alert', methods=['POST'])
def send_risk_alert():
    data = request.get_json()
    token = data.get('fcm_token')
    title = data.get('title', 'FloodShield Emergency Alert')
    body = data.get('body', 'High risk of flooding detected in your area!')
    
    if not token:
        return jsonify({"status": "error", "message": "FCM device token is required"}), 400
        
    if not FIREBASE_INITIALIZED:
        return jsonify({
            "status": "success", 
            "message": "Firebase mock mode: Alert logic processed successfully!"
        }), 200

    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            token=token,
        )
        response = messaging.send(message)
        return jsonify({
            "status": "success",
            "message": "Risk alert notification sent successfully via Firebase!",
            "firebase_response": response
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Application Runner
if __name__ == '__main__':
    app.run(debug=True)