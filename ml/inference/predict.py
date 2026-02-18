import joblib

category_model = joblib.load("ml/models/category_model.pkl")
urgency_model = joblib.load("ml/models/urgency_model.pkl")

def predict_ticket(message: str):
    category = category_model.predict([message])[0]
    urgency = urgency_model.predict([message])[0]

    cat_proba = max(category_model.predict_proba([message])[0])
    urg_proba = max(urgency_model.predict_proba([message])[0])

    confidence = (cat_proba + urg_proba) / 2

    return {
        "category": category,
        "urgency": urgency,
        "confidence": float(confidence)
    }

if __name__ == "__main__":
    result = predict_ticket("My payment failed")
    print(result)
