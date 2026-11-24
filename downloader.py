import json
from pathlib import Path

HISTORY_FILE = Path(__file__).resolve().parent / "history.json"

def load_history():
    try:
        if HISTORY_FILE.exists():
            data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        pass
    return []

def save_history(items):
    HISTORY_FILE.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
