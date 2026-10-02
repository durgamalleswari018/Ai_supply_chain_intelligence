from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return jsonify({
        "status": "success",
        "message": "SupplyIQ AI Supply Chain Intelligence API is running"
    })

@app.route("/api/health")
def health():
    return jsonify({
        "status": "healthy"
    })

@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True) or {}

    return jsonify({
        "status": "success",
        "message": "Supply chain data received successfully",
        "data": data
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
