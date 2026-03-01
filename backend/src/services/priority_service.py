from typing import Any

# Priority scale:
# 1 = highest priority, 4 = lowest priority
MIN_PRIORITY = 1
MAX_PRIORITY = 4

URGENCY_TO_PRIORITY = {
    "high": 1,
    "medium": 2,
    "low": 3,
}

# Category modifiers move the base priority up/down.
# Negative number => more urgent (closer to P1)
CATEGORY_PRIORITY_MODIFIERS = {
    "technical": -1,
    "account": 0,
    "billing": 0,
}


def _clamp_priority(value: int) -> int:
    return max(MIN_PRIORITY, min(MAX_PRIORITY, value))


def normalize_urgency(urgency: str | None) -> str:
    normalized = (urgency or "medium").strip().lower()
    if normalized not in URGENCY_TO_PRIORITY:
        return "medium"
    return normalized


def normalize_priority(raw_priority: Any) -> int | None:
    if raw_priority is None:
        return None
    try:
        parsed = int(raw_priority)
    except (TypeError, ValueError):
        return None
    return _clamp_priority(parsed)


def calculate_priority(
    category: str | None,
    urgency: str | None,
    confidence: float | None,
    ml_priority: Any = None,
) -> int:
    parsed_ml_priority = normalize_priority(ml_priority)
    if parsed_ml_priority is not None:
        # If model explicitly provides priority, trust it after normalization.
        return parsed_ml_priority

    normalized_urgency = normalize_urgency(urgency)
    base_priority = URGENCY_TO_PRIORITY[normalized_urgency]

    normalized_category = (category or "").strip().lower()
    category_modifier = CATEGORY_PRIORITY_MODIFIERS.get(normalized_category, 0)
    priority = base_priority + category_modifier

    # Low-confidence predictions should avoid auto-escalating to critical.
    if confidence is None or confidence < 0.60:
        priority += 1

    return _clamp_priority(priority)
