import requests

url = "http://127.0.0.1:5000/api/reports"

payload = {
    "location": "Adajan, Surat",
    "latitude": 21.1859,
    "longitude": 72.8089,
    "description": "Heavy water logging near main road",
    "severity": "High"
}

response = requests.post(url, json=payload)

print("Status Code:", response.status_code)
print("Response JSON:", response.json())