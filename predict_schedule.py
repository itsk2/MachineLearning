import pandas as pd
import pymongo
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta
import hashlib

client = pymongo.MongoClient("mongodb+srv://nowaste:uD2H_z_apa8DSsn@nowastecluster.egudtya.mongodb.net/nowaste?retryWrites=true&w=majority")
db = client["nowaste"]
collection = db["sacks"]

def convert_stall_to_numeric(stall):
    return int(hashlib.md5(str(stall).encode()).hexdigest(), 16) % (10 ** 8 )

def optimal_schedule():
    cursor = collection.find({}, {"createdAt": 1, "kilo": 1, "stallNumber": 1, "_id": 0})  
    df = pd.DataFrame(list(cursor))

    if df.empty:
        return {"error": "No data available"}  # ✅ Return dict instead of jsonify()

    df["createdAt"] = pd.to_datetime(df["createdAt"])
    df["day_of_week"] = df["createdAt"].dt.dayofweek
    df["month"] = df["createdAt"].dt.month
    df["year"] = df["createdAt"].dt.year
    df["kilo"] = df["kilo"].astype(float)
    print(df)  # Check if data is loaded correctly
    df["stallNumber"] = df["stallNumber"].apply(convert_stall_to_numeric)

    X = df[["day_of_week", "month", "year", "stallNumber"]]
    y = df["kilo"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = LinearRegression()
    model.fit(X_train, y_train)

    future_dates = []
    stalls = collection.distinct("stallNumber")
    for i in range(1, 15):
        for stall in stalls:
            stall_numeric = convert_stall_to_numeric(stall)
            future_dates.append({
                "day_of_week": (datetime.today() + timedelta(days=i)).weekday(),
                "month": (datetime.today() + timedelta(days=i)).month,
                "year": (datetime.today() + timedelta(days=i)).year,
                "stallNumber": stall_numeric,
                "date": (datetime.today() + timedelta(days=i)).strftime("%Y-%m-%d")
            })

    future_df = pd.DataFrame(future_dates)
    predictions = model.predict(future_df[["day_of_week", "month", "year", "stallNumber"]])
    print(f"Predicted values: {predictions}")  # Debugging output

    collection_threshold = 5 

    stall_mapping = {convert_stall_to_numeric(stall): stall for stall in stalls}
    optimal_schedule = []

    for i, pred in enumerate(predictions):
        stall_num = stall_mapping[future_dates[i]["stallNumber"]]
        if pred >= collection_threshold:
            optimal_schedule.append({
                "date": future_dates[i]["date"],
                "stallNumber": stall_num,
                "predicted_kilos": round(pred, 2)
            })

    return optimal_schedule