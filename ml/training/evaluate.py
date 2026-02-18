import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

DATA_PATH = Path("ml/training/tickets.csv")
CATEGORY_MODEL_PATH = Path("ml/models/category_model.pkl")
URGENCY_MODEL_PATH = Path("ml/models/urgency_model.pkl")
METRICS_PATH = Path("ml/models/metrics.json")
REPORT_PATH = Path("ml/models/eval_report.txt")


def main() -> None:
    df = pd.read_csv(DATA_PATH)

    x = df["message"]
    y_category = df["category"]
    y_urgency = df["urgency"]

    _, x_test, _, y_cat_test, _, y_urg_test = train_test_split(
        x,
        y_category,
        y_urgency,
        test_size=0.2,
        random_state=42,
        stratify=y_category,
    )

    category_model = joblib.load(CATEGORY_MODEL_PATH)
    urgency_model = joblib.load(URGENCY_MODEL_PATH)

    cat_pred = category_model.predict(x_test)
    urg_pred = urgency_model.predict(x_test)

    metrics = {
        "category_accuracy": float(accuracy_score(y_cat_test, cat_pred)),
        "urgency_accuracy": float(accuracy_score(y_urg_test, urg_pred)),
    }

    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    report_text = [
        "CATEGORY REPORT\n",
        classification_report(y_cat_test, cat_pred),
        "\nURGENCY REPORT\n",
        classification_report(y_urg_test, urg_pred),
    ]
    REPORT_PATH.write_text("\n".join(report_text), encoding="utf-8")

    print("Evaluation complete. Metrics saved.")


if __name__ == "__main__":
    main()
