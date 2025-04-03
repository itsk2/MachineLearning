from flask import Flask, jsonify
from waste_prediction import predict_waste
from predict_schedule import optimal_schedule
from collected_progress import waste_collected_progress
from waste_generation_trend import waste_generation_trend

app = Flask(__name__)

@app.route("/api/v1/ml/predict-waste", methods=["GET"])
def get_predicted_waste():
    return jsonify(predict_waste())

@app.route("/api/v1/ml/optimal-collection-schedule", methods=["GET"])
def get_predicted_collection_schedule():
    return jsonify(optimal_schedule())

@app.route("/api/v1/ml/waste-collected-progress", methods=["GET"])
def get_waste_collected_progress():
    return jsonify(waste_collected_progress())

@app.route("/api/v1/ml/waste-generation-trend", methods=["GET"])
def get_waste_generation_trend():
    return jsonify(waste_generation_trend())

if __name__== "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)