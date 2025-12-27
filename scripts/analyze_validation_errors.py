from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, Counter

# =====================
# config
# =====================

LOG_FILE = Path("logs/validation_errors.jsonl")

THRESHOLD = 3        # 何回出たら昇格候補か
WINDOW_HOURS = 24    # 直近何時間を見るか

# =====================
# helpers
# =====================

def parse_ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts)

# =====================
# main analyze
# =====================

def main():
    if not LOG_FILE.exists():
        print("[WARN] log file not found:", LOG_FILE)
        print("No validation errors found.")
        return

    now = datetime.utcnow()
    window_start = now - timedelta(hours=WINDOW_HOURS)

    # rule -> (target -> count)
    warning_counter: dict[str, Counter] = defaultdict(Counter)

    with LOG_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)

            ts = parse_ts(record["ts"])
            if ts < window_start:
                continue

            for err in record.get("errors", []):
                if err.get("severity") != "warning":
                    continue

                rule = err.get("rule")
                target = err.get("target")

                if not rule or not target:
                    continue

                warning_counter[rule][target] += 1

    # =====================
    # output
    # =====================

    print("\n=== 🔼 Auto Escalation Candidates ===")

    promoted_any = False

    for rule, counter in warning_counter.items():
        candidates = {
            target: count
            for target, count in counter.items()
            if count >= THRESHOLD
        }

        if not candidates:
            continue

        promoted_any = True
        print(f"\n[{rule}]")

        for target, count in candidates.items():
            print(f"  - {target}: {count} warnings → 🔺 promote to ERROR")

    if not promoted_any:
        print("\n(no promotion candidates found)")


if __name__ == "__main__":
    main()
