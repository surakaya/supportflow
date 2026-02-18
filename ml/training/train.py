import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report

# Dataset yükle
df = pd.read_csv("ml/training/tickets.csv")

X = df["message"]
y_category = df["category"]
y_urgency = df["urgency"]

# Train test split
X_train, X_test, y_cat_train, y_cat_test, y_urg_train, y_urg_test = train_test_split(
    X,
    y_category,
    y_urgency,
    test_size=0.2,
    random_state=42
)

# Category modeli
category_model = Pipeline([
    ("tfidf", TfidfVectorizer()),
    ("clf", LogisticRegression(max_iter=1000, class_weight="balanced"))
])

category_model.fit(X_train, y_cat_train)

# Urgency modeli
urgency_model = Pipeline([
    ("tfidf", TfidfVectorizer()),
    ("clf", LogisticRegression(max_iter=1000))
])

urgency_model.fit(X_train, y_urg_train)

# Kaydet
joblib.dump(category_model, "ml/models/category_model.pkl")
joblib.dump(urgency_model, "ml/models/urgency_model.pkl")

print("Model eğitildi ve kaydedildi.")


from sklearn.metrics import accuracy_score
import json

# Test set tahminleri
cat_pred = category_model.predict(X_test)
urg_pred = urgency_model.predict(X_test)

cat_acc = accuracy_score(y_cat_test, cat_pred)
urg_acc = accuracy_score(y_urg_test, urg_pred)

metrics = {
    "category_accuracy": float(cat_acc),
    "urgency_accuracy": float(urg_acc)
}

with open("ml/models/metrics.json", "w") as f:
    json.dump(metrics, f, indent=4)

print("Metrics kaydedildi.")
