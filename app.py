from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
CORS(
    app
)  # Frontend aur backend ke beech CORS errors avoid karne ke liye enabled hai

# SQLite Database Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///flood_shield.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# Database Model for Flood Risk Logs & History
class FloodLog(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  timestamp = db.Column(db.DateTime, default=datetime.utcnow)
  rainfall = db.Column(db.Float)  # in mm/h
  water_level = db.Column(db.Float)  # in meters
  risk_status = db.Column(db.String(20))  # CRITICAL / MODERATE / LOW

  def to_dict(self):
    return {
        "id": self.id,
        "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "rainfall": self.rainfall,
        "water_level": self.water_level,
        "risk_status": self.risk_status,
    }


# Create database tables within application context
with app.app_context():
  db.create_all()


@app.route("/")
def home():
  return jsonify({
      "status": "success",
      "message": "Welcome to FloodShield Backend API (SSIP SFIC 2026)",
      "team_id": "TM004301",
  })


@app.route("/api/weather", methods=["GET"])
def get_weather_and_risk():
  import random

  # Simulated live sensor data generation
  rainfall = round(random.uniform(5.0, 50.0), 2)
  water_level = round(random.uniform(4.0, 10.0), 2)

  # Rule-based risk assessment engine
  if water_level > 8.5 or rainfall > 35.0:
    risk_status = "CRITICAL"
  elif water_level > 6.5 or rainfall > 15.0:
    risk_status = "MODERATE"
  else:
    risk_status = "LOW"

  # Save record into SQLite database
  new_log = FloodLog(
      rainfall=rainfall, water_level=water_level, risk_status=risk_status
  )
  db.session.add(new_log)
  db.session.commit()

  return jsonify({
      "rainfall_mm_h": rainfall,
      "water_level_m": water_level,
      "risk_status": risk_status,
      "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
  })


@app.route("/api/history", methods=["GET"])
def get_history():
  # Fetch recent logs from database
  logs = FloodLog.query.order_by(FloodLog.timestamp.desc()).limit(10).all()
  return jsonify([log.to_dict() for log in logs])


if __name__ == "__main__":
  app.run(debug=True, port=5000)