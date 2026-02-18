def urgency_to_priority(urgency: str | None) -> int:
    mapping = {
        "high": 1,
        "medium": 2,
        "low": 3,
    }
    return mapping.get((urgency or "").lower(), 3)
