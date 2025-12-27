# scripts/auto_promote_rules.py
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
import yaml

LOG_FILE = Path("logs/validation_errors.jsonl")
RULE_FILE = Path("data/rules/rules.yaml")


def parse_ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts)


def load_rules() -> dict:
    if not RULE_FILE.exists():
        return {}
    with RULE_FILE.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_rules(rules: dict):
    RULE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with RULE_FILE.open("w", encoding="utf-8") as f:
        yaml.safe_dump(
            rules,
            f,
            allow_unicode=True,
            sort_keys=False,
        )


def main():
    if not LOG_FILE.exists():
        print("(no promotions applied)")
        return

    rules = load_rules()
    now = datetime.utcnow()

    # rule -> target -> stats
    stats = defaultdict(lambda: {
        "count": 0,
        "first_seen": None,
        "last_seen": None,
    })

    with LOG_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            ts = parse_ts(rec["ts"])

            for e in rec.get("errors", []):
                if e.get("severity") != "warning":
                    continue

                rule = e.get("rule")
                target = e.get("target")

                if rule not in rules:
                    continue

                ap = rules[rule].get("auto_promote", {})
                if not ap.get("enabled"):
                    continue

                window = ap.get("window_hours", 24)
                if ts < now - timedelta(hours=window):
                    continue

                key = (rule, target)
                s = stats[key]
                s["count"] += 1
                s["first_seen"] = min(s["first_seen"], ts) if s["first_seen"] else ts
                s["last_seen"] = max(s["last_seen"], ts) if s["last_seen"] else ts

    promoted = False

    for (rule, target), s in stats.items():
        rule_def = rules[rule]

        if rule_def.get("promoted"):
            continue

        threshold = rule_def["auto_promote"].get("threshold", 999)
        if s["count"] < threshold:
            continue

        # ---- 昇格 ----
        rule_def["severity"] = "error"
        rule_def["promoted"] = True
        rule_def["promoted_at"] = s["last_seen"].isoformat(timespec="seconds")

        rule_def["promoted_reason"] = {
            "threshold": threshold,
            "count": s["count"],
            "window_hours": rule_def["auto_promote"].get("window_hours"),
            "first_seen": s["first_seen"].isoformat(timespec="seconds"),
            "last_seen": s["last_seen"].isoformat(timespec="seconds"),
            "targets": [target],
        }

        # target_severity も確実に error に
        rule_def.setdefault("target_severity", {})
        rule_def["target_severity"][target] = "error"

        promoted = True
        print(f"[PROMOTE] {rule}: {target} ({s['count']}) → error")

    if promoted:
        save_rules(rules)
        print("\n✅ rules.yaml updated (with promoted_reason)")
    else:
        print("(no promotions applied)")


if __name__ == "__main__":
    main()
