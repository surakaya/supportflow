from functools import lru_cache
from pathlib import Path
import re

import joblib

LOW_CONFIDENCE_THRESHOLD = 0.55

CATEGORY_KEYWORDS = {
    "account": [
        "sifre", "şifre", "parola", "hesap", "hesab", "oturum", "giris", "giriş",
        "kilitl", "kapand", "2fa", "dogrulama", "doğrulama",
    ],
    "billing": [
        "fatura", "odeme", "ödeme", "iade", "kart", "abonelik", "ucret",
        "ücret", "tahsil", "paket", "plan",
    ],
    "technical": [
        "hata", "cokuyor", "çöküyor", "yavas", "yavaş", "donuyor", "yanit",
        "yanıt", "api", "timeout", "baglan", "bağlan", "500",
    ],
}

HIGH_URGENCY_KEYWORDS = [
    "acil", "kritik", "yaniyor", "yanıyor", "calisam", "çalışam", "blok",
    "durdu", "cop", "çöp", "hemen",
]


def _normalize_text(text: str) -> str:
    lowered = text.lower()
    # Keep Turkish characters but collapse whitespace/punctuation.
    return re.sub(r"\s+", " ", lowered).strip()


def _rule_based_fallback(text: str) -> tuple[str, str]:
    normalized = _normalize_text(text)
    category = "technical"
    matched = False

    for candidate, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            category = candidate
            matched = True
            break

    if any(keyword in normalized for keyword in HIGH_URGENCY_KEYWORDS):
        urgency = "high"
    elif matched:
        urgency = "medium"
    else:
        urgency = "low"

    return category, urgency


def _models_dir() -> Path:
    project_root = Path(__file__).resolve().parents[3]
    return project_root / "ml" / "models"


@lru_cache(maxsize=1)
def _load_models():
    models_dir = _models_dir()
    category_model_path = models_dir / "category_model.pkl"
    urgency_model_path = models_dir / "urgency_model.pkl"

    if not category_model_path.exists() or not urgency_model_path.exists():
        raise FileNotFoundError(
            f"Missing model files under {models_dir}. "
            "Run `dvc repro` to generate model artifacts."
        )

    category_model = joblib.load(category_model_path)
    urgency_model = joblib.load(urgency_model_path)
    return category_model, urgency_model


def analyze_text(text: str) -> dict:
    category_model, urgency_model = _load_models()

    category = category_model.predict([text])[0]
    urgency = urgency_model.predict([text])[0]

    category_conf = float(max(category_model.predict_proba([text])[0]))
    urgency_conf = float(max(urgency_model.predict_proba([text])[0]))
    confidence = (category_conf + urgency_conf) / 2.0

    # Low-confidence outputs tend to collapse to a default class for out-of-domain text.
    # Use deterministic keyword fallback to avoid obviously wrong labels.
    if confidence < LOW_CONFIDENCE_THRESHOLD:
        fallback_category, fallback_urgency = _rule_based_fallback(text)
        category = fallback_category
        urgency = fallback_urgency

    return {
        "category": category,
        "urgency": urgency,
        "confidence": confidence,
    }
