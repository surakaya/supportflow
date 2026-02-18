import pandas as pd
import joblib
from sklearn.metrics import classification_report

df = pd.read_csv("ml/training/tickets.csv")

X = df["message"]
y_category = df["category"]
y_urgency = df["urgency"]

category_model = joblib.load("ml/models/category_model.pkl")
urgency_model = joblib.load("ml/models/urgency_model.pkl")

cat_pred = category_model.predict(X_test)
urg_pred = urgency_model.predict(X_test)

print("CATEGORY REPORT")
print(classification_report(y_category, cat_pred))

print("URGENCY REPORT")
print(classification_report(y_urgency, urg_pred))
