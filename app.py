from flask import Flask, render_template
import requests
import base64

app = Flask(__name__)

@app.route("/")
def home():
    login_url = "https://IP-Address/restapi/v3.2/login"
    payload = {"username": "Enter-Username", "password": "Enter-Password"}

    headers = {
        "Content-Type" : "application/json"
    }

    token = requests.post(login_url, json=payload, verify = False).json().get("token")

    encoded_token = base64.b64encode(f"{token}:".encode()).decode()

    services_url = "https://IP-Address/restapi/v3.2/services"

    payload = {}

    headers = {
        'Authorization': f'Basic {encoded_token}'
    }

    services_response = requests.request("GET", services_url, headers=headers, data = payload, verify = False)

    services_json = services_response.json()

    services = services_response.text

    return render_template("dashboard.html", services=services)

if __name__ == "__main__":
    app.run(debug=True)