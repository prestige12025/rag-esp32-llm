# rag/fix_history.py
from pathlib import Path
from datetime import datetime
import json

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_FILE = LOG_DIR / "fix_history.jsonl"


def record_fix(
    *,
    source: str,
    chunk_index: int,
    rule: str,
    errors_before: list[str],
    original_text: str,
    fixed_text: str,
    errors_after: list[str],
):
    LOG_DIR.mkdir(exist_ok=True)

    record = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "source": source,
        "chunk_index": chunk_index,
        "rule": rule,
        "errors_before": errors_before,
        "errors_after": errors_after,
        "original_text": original_text,
        "fixed_text": fixed_text,
    }

    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
