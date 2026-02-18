from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

DATA_PATH = Path("ml/training/tickets.csv")
MODELS_DIR = Path("ml/models")
CATEGORY_MODEL_PATH = MODELS_DIR / "category_model.pkl"
URGENCY_MODEL_PATH = MODELS_DIR / "urgency_model.pkl"


def main() -> None:
    df = pd.read_csv(DATA_PATH)

    x = df["message"]
    y_category = df["category"]
    y_urgency = df["urgency"]

    x_train, _, y_cat_train, _, y_urg_train, _ = train_test_split(
        x,
        y_category,
        y_urgency,
        test_size=0.2,
        random_state=42,
        stratify=y_category,
    )

    category_model = Pipeline(
        [
            ("tfidf", TfidfVectorizer()),
            ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ]
    )
    category_model.fit(x_train, y_cat_train)

    urgency_model = Pipeline(
        [
            ("tfidf", TfidfVectorizer()),
            ("clf", LogisticRegression(max_iter=1000)),
        ]
    )
    urgency_model.fit(x_train, y_urg_train)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(category_model, CATEGORY_MODEL_PATH)
    joblib.dump(urgency_model, URGENCY_MODEL_PATH)

    print("Training complete. Models saved.")


if __name__ == "__main__":
    main()
