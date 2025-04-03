import pymongo
import pandas as pd
from prophet import Prophet
from datetime import datetime, timedelta

def waste_generation_trend():
    # Connect to MongoDB
    client = pymongo.MongoClient("mongodb+srv://nowaste:uD2H_z_apa8DSsn@nowastecluster.egudtya.mongodb.net/nowaste?retryWrites=true&w=majority")
    db = client["nowaste"]
    sacks_collection = db["sacks"]

    # Get current date and filter data from the past 7 days
    today = datetime.utcnow()
    last_week = today - timedelta(days=29)

    # Fetch last 7 days of data
    sacks = sacks_collection.find(
        {"createdAt": {"$gte": last_week}},  # Filter only recent 7 days
        {"createdAt": 1, "kilo": 1}
    )

    # Convert to DataFrame
    data = [{"ds": sack["createdAt"], "y": float(sack["kilo"])} for sack in sacks]
    
    if not data:  # Handle case where no data is found
        return {"error": "Not enough data for prediction"}

    df = pd.DataFrame(data)
    df["ds"] = pd.to_datetime(df["ds"])

    # Train Prophet model
    model = Prophet()
    model.fit(df)

    # Predict future waste collection for the next 7 days
    future = model.make_future_dataframe(periods=7)
    forecast = model.predict(future)

    # Extract relevant data
    predictions = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]]

    return predictions.to_dict(orient="records")