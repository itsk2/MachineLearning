import pymongo
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta

def waste_collected_progress():
    # Connect to MongoDB
    client = pymongo.MongoClient("mongodb+srv://nowaste:uD2H_z_apa8DSsn@nowastecluster.egudtya.mongodb.net/nowaste?retryWrites=true&w=majority")
    db = client["nowaste"]
    pickups_collection = db["pickups"]
    
    # Fetch completed pickups
    completed_pickups = pickups_collection.find({"status": "completed"})
    
    # Process data
    data = []
    for pickup in completed_pickups:
        pickup_date = pickup.get("pickupTimestamp") or pickup.get("createdAt")
        if pickup_date:
            pickup_date = datetime.fromisoformat(pickup_date) if isinstance(pickup_date, str) else pickup_date
            pickup_date = pickup_date.date()
            total_kilo = float(pickup.get("totalKilo", 0))
            data.append({"date": pickup_date, "total_kilo": total_kilo})
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    if df.empty:
        return {"message": "No data available for prediction"}
    
    df = df.groupby("date").sum().reset_index()
    df["date"] = pd.to_datetime(df["date"])
    df["day"] = (df["date"] - df["date"].min()).dt.days
    
    # Train Linear Regression Model
    X = df[["day"]]
    y = df["total_kilo"]
    model = LinearRegression()
    model.fit(X, y)
    
    # Predict future waste for the next 7 days
    future_dates = [df["date"].max() + timedelta(days=i) for i in range(1, 8)]
    future_days = [(d - df["date"].min()).days for d in future_dates]
    future_predictions = model.predict(np.array(future_days).reshape(-1, 1))
    
    # Format results
    predictions = [{"date": str(future_dates[i]), "predicted_kilos": round(future_predictions[i], 2)} for i in range(7)]
    
    return {"past_data": df.to_dict(orient="records"), "predictions": predictions}