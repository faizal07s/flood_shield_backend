from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity
)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(
    app
)  # Frontend aur backend ke beech CORS errors avoid karne ke liye enabled hai

# SQLite Database Configuration
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

jwt = JWTManager(app)
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

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email
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

#registration auth api
@app.route("/api/auth/register", methods=["POST"])
def register():

    data = request.get_json(silent=True) or {}

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not name or not email or not password:
        return jsonify({
            "status": "error",
            "message": "All fields are required"
        }), 400

    if len(password) < 8:
        return jsonify({
            "status": "error",
            "message": "Password must be at least 8 characters"
        }), 400

    existing_user = User.query.filter_by(email=email).first()

    if existing_user:
        return jsonify({
            "status": "error",
            "message": "Email already registered"
        }), 409

    hashed_password = generate_password_hash(password)

    new_user = User(
        name=name,
        email=email,
        password=hashed_password
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "status": "success",
        "message": "Registration successful",
        "user": new_user.to_dict()
    }), 201

#login api
@app.route("/api/auth/login", methods=["POST"])
def login():

    data = request.get_json(silent=True) or {}

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({
            "status": "error",
            "message": "Email and password are required"
        }), 400

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(
        user.password, password
    ):
        return jsonify({
            "status": "error",
            "message": "Invalid email or password"
        }), 401

    access_token = create_access_token(
        identity=str(user.id)
    )

    return jsonify({
        "status": "success",
        "message": "Login successful",
        "access_token": access_token,
        "user": user.to_dict()
    }), 200

'''
Maintain login sessions when reopening the mobile app
used to Display the logged-in user's name on the dashboard.
Show their profile.
Associate flood alerts with a particular user.
Save user-specific location preferences.
Maintain login sessions when reopening the mobile app'''
@app.route("/api/auth/me", methods=["GET"])
@jwt_required()
def get_current_user():

    user_id = get_jwt_identity()

    user = db.session.get(User, int(user_id))

    if not user:
        return jsonify({
            "status": "error",
            "message": "User not found"
        }), 404

    return jsonify({
        "status": "success",
        "user": user.to_dict()
    }), 200

if __name__ == "__main__":
  app.run(debug=True, port=5000)