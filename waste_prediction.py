from flask import Flask, request, jsonify
import pandas as pd
import pymongo
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta
import hashlib

app = Flask(__name__)

# Connect to MongoDB
client = pymongo.MongoClient("mongodb+srv://nowaste:uD2H_z_apa8DSsn@nowastecluster.egudtya.mongodb.net/nowaste?retryWrites=true&w=majority")
db = client["nowaste"]
collection = db["sacks"]

# Convert stall numbers to unique numeric identifiers (hashing approach)
def convert_stall_to_numeric(stall):
    return int(hashlib.md5(str(stall).encode()).hexdigest(), 16) % (10 ** 8)

def fetch_data():
    cursor = collection.find({}, {"createdAt": 1, "kilo": 1, "stallNumber": 1, "_id": 0})
    df = pd.DataFrame(list(cursor))

    if df.empty or "createdAt" not in df or "kilo" not in df or "stallNumber" not in df:
        return None

    df["createdAt"] = pd.to_datetime(df["createdAt"])
    df["day_of_week"] = df["createdAt"].dt.dayofweek
    df["month"] = df["createdAt"].dt.month
    df["year"] = df["createdAt"].dt.year
    df["kilo"] = df["kilo"].astype(float)

    # Convert stallNumber to unique numeric format
    df["stallNumber"] = df["stallNumber"].apply(convert_stall_to_numeric)

    return df[["day_of_week", "month", "year", "stallNumber", "kilo"]]

@app.route("/api/v1/ml/predict-waste", methods=["GET"])
def predict_waste():
    data = fetch_data()
    
    if data is None:
        return jsonify({"error": "No data available"}), 400

    X = data[["day_of_week", "month", "year", "stallNumber"]]
    y = data["kilo"]

    # Train the model
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = LinearRegression()
    model.fit(X_train, y_train)

    # Get all unique stall numbers (converted)
    stall_numbers = collection.distinct("stallNumber")
    stall_numbers = list(set(map(convert_stall_to_numeric, stall_numbers)))  # Convert and remove duplicates

    # Generate predictions for the next 7 days for each stall
    future_dates = []
    for i in range(1, 8):  # Predict for the next 7 days
        for stall in stall_numbers:  # Predict for each stall
            future_dates.append({
                "day_of_week": (datetime.today() + timedelta(days=i)).weekday(),
                "month": (datetime.today() + timedelta(days=i)).month,
                "year": (datetime.today() + timedelta(days=i)).year,
                "stallNumber": stall,
                "date": (datetime.today() + timedelta(days=i)).strftime("%Y-%m-%d")
            })

    # Convert to DataFrame
    future_df = pd.DataFrame(future_dates)

    # Make predictions
    predictions = model.predict(future_df[["day_of_week", "month", "year", "stallNumber"]])

    # Convert back to original stall names
    stall_mapping = {convert_stall_to_numeric(stall): stall for stall in collection.distinct("stallNumber")}

    # Format response
    prediction_results = [
        {
            "date": future_dates[i]["date"],
            "stallNumber": stall_mapping[future_dates[i]["stallNumber"]],
            "predicted_kilos": round(pred, 2)
        }
        for i, pred in enumerate(predictions)
    ]

    return prediction_results