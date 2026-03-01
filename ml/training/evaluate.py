import json
import math
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline

DATA_PATH = Path("ml/training/tickets.csv")
CATEGORY_MODEL_PATH = Path("ml/models/category_model.pkl")
URGENCY_MODEL_PATH = Path("ml/models/urgency_model.pkl")
METRICS_PATH = Path("ml/models/metrics.json")
REPORT_PATH = Path("ml/models/eval_report.txt")
TEST_SIZE = 0.2
RANDOM_STATE = 42


def load_clean_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    df = df.dropna(subset=["message", "category", "urgency"]).copy()
    df["message"] = df["message"].astype(str).str.strip()
    df = df[df["message"] != ""]
    # Keep one row per message to avoid train/test leakage by duplicates.
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


def build_category_pipeline() -> Pipeline:
    return Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)),
            ("clf", LogisticRegression(max_iter=1200, class_weight="balanced")),
        ]
    )


def build_urgency_pipeline() -> Pipeline:
    return Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)),
            ("clf", LogisticRegression(max_iter=1200, class_weight="balanced")),
        ]
    )


def cv_macro_f1(model: Pipeline, x_train: pd.Series, y_train: pd.Series) -> tuple[float, float]:
    min_class_count = int(y_train.value_counts().min())
    folds = max(2, min(5, min_class_count))
    cv = StratifiedKFold(n_splits=folds, shuffle=True, random_state=RANDOM_STATE)
    scores = cross_val_score(model, x_train, y_train, scoring="f1_macro", cv=cv, n_jobs=None)
    return float(np.mean(scores)), float(np.std(scores))


def main() -> None:
    df = load_clean_data()

    x = df["message"]
    y_category = df["category"]
    y_urgency = df["urgency"]
    y_joint = y_category.astype(str) + "__" + y_urgency.astype(str)
    stratify_target = choose_stratify_target(y_joint, y_category, len(df))

    x_train, x_test, y_cat_train, y_cat_test, y_urg_train, y_urg_test = train_test_split(
        x,
        y_category,
        y_urgency,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=stratify_target,
    )

    category_model = joblib.load(CATEGORY_MODEL_PATH)
    urgency_model = joblib.load(URGENCY_MODEL_PATH)

    cat_pred = category_model.predict(x_test)
    urg_pred = urgency_model.predict(x_test)

    category_cv_mean, category_cv_std = cv_macro_f1(build_category_pipeline(), x_train, y_cat_train)
    urgency_cv_mean, urgency_cv_std = cv_macro_f1(build_urgency_pipeline(), x_train, y_urg_train)

    category_labels = sorted(y_cat_test.unique().tolist())
    urgency_labels = sorted(y_urg_test.unique().tolist())

    category_cm = confusion_matrix(y_cat_test, cat_pred, labels=category_labels)
    urgency_cm = confusion_matrix(y_urg_test, urg_pred, labels=urgency_labels)

    metrics = {
        "test_samples": int(len(x_test)),
        "category_holdout_accuracy": float(accuracy_score(y_cat_test, cat_pred)),
        "category_holdout_macro_f1": float(f1_score(y_cat_test, cat_pred, average="macro")),
        "urgency_holdout_accuracy": float(accuracy_score(y_urg_test, urg_pred)),
        "urgency_holdout_macro_f1": float(f1_score(y_urg_test, urg_pred, average="macro")),
        "category_cv_macro_f1_mean": category_cv_mean,
        "category_cv_macro_f1_std": category_cv_std,
        "urgency_cv_macro_f1_mean": urgency_cv_mean,
        "urgency_cv_macro_f1_std": urgency_cv_std,
        "category_labels": category_labels,
        "urgency_labels": urgency_labels,
        "category_confusion_matrix": category_cm.tolist(),
        "urgency_confusion_matrix": urgency_cm.tolist(),
    }

    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    report_text = [
        "CATEGORY REPORT\n",
        classification_report(y_cat_test, cat_pred, zero_division=0),
        "\nURGENCY REPORT\n",
        classification_report(y_urg_test, urg_pred, zero_division=0),
    ]
    REPORT_PATH.write_text("\n".join(report_text), encoding="utf-8")

    print("Evaluation complete. Metrics saved.")


if __name__ == "__main__":
    main()
