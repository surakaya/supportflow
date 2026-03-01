import math
import json
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
MODEL_METADATA_PATH = MODELS_DIR / "model_metadata.json"
TEST_SIZE = 0.2
RANDOM_STATE = 42


def load_clean_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    df = df.dropna(subset=["message", "category", "urgency"]).copy()
    df["message"] = df["message"].astype(str).str.strip()
    df = df[df["message"] != ""]
    # Prevent the same message text from leaking into both train and test.
    df = df.drop_duplicates(subset=["message"], keep="first")
    return df


def can_stratify(target: pd.Series, n_samples: int, test_size: float) -> bool:
    class_counts = target.value_counts()
    if class_counts.empty or class_counts.min() < 2:
        return False

    n_test = math.ceil(n_samples * test_size)
    n_classes = int(class_counts.shape[0])
    return n_test >= n_classes


def choose_stratify_target(y_joint: pd.Series, y_category: pd.Series, n_samples: int) -> pd.Series | None:
    if can_stratify(y_joint, n_samples, TEST_SIZE):
        return y_joint
    if can_stratify(y_category, n_samples, TEST_SIZE):
        return y_category
    return None


def main() -> None:
    df = load_clean_data()

    x = df["message"]
    y_category = df["category"]
    y_urgency = df["urgency"]
    y_joint = y_category.astype(str) + "__" + y_urgency.astype(str)
    stratify_target = choose_stratify_target(y_joint, y_category, len(df))

    x_train, _, y_cat_train, _, y_urg_train, _ = train_test_split(
        x,
        y_category,
        y_urgency,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=stratify_target,
    )

    category_model = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)),
            ("clf", LogisticRegression(max_iter=1200, class_weight="balanced")),
        ]
    )
    category_model.fit(x_train, y_cat_train)

    urgency_model = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)),
            ("clf", LogisticRegression(max_iter=1200, class_weight="balanced")),
        ]
    )
    urgency_model.fit(x_train, y_urg_train)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(category_model, CATEGORY_MODEL_PATH)
    joblib.dump(urgency_model, URGENCY_MODEL_PATH)

    metadata = {
        "model_type": "TF-IDF + LogisticRegression",
        "random_state": RANDOM_STATE,
        "test_size": TEST_SIZE,
        "total_samples": int(len(df)),
        "train_samples": int(len(x_train)),
        "holdout_samples": int(len(df) - len(x_train)),
        "category_features": int(len(category_model.named_steps["tfidf"].vocabulary_)),
        "urgency_features": int(len(urgency_model.named_steps["tfidf"].vocabulary_)),
    }
    with open(MODEL_METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print("Training complete. Models saved.")


if __name__ == "__main__":
    main()
