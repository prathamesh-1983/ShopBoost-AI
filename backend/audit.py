import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
AUDIT_FILE = BASE_DIR / "audit_log.json"


def log_event(event_type, details):

    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": event_type,
        "details": details
    }

    existing = []

    if AUDIT_FILE.exists():

        try:
            with open(AUDIT_FILE, "r", encoding="utf-8") as file:
                existing = json.load(file)

        except json.JSONDecodeError:
            existing = []

    existing.append(event)

    with open(AUDIT_FILE, "w", encoding="utf-8") as file:
        json.dump(
            existing,
            file,
            indent=4
        )