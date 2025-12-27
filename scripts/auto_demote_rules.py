# scripts/auto_demote_rules.py
from __future__ import annotations

import json
import yaml
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

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

def load_last_seen() -> dict:
    """
    rule -> target -> last_seen(datetime)
    """
    last_seen = defaultdict(dict)

    if not LOG_FILE.exists():
        return last_seen

    with LOG_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            ts = parse_ts(rec["ts"])

            for e in rec.get("errors", []):
                rule = e.get("rule")
                target = e.get("target")
                if rule and target:
                    prev = last_seen.get(rule, {}).get(target)
                    if not prev or ts > prev:
                        last_seen.setdefault(rule, {})[target] = ts

    return last_seen

def main():
    rules = load_rules()
    last_seen = load_last_seen()
    now = datetime.utcnow()

    demoted = False

    for rule_name, rule_def in rules.items():
        auto_demote = rule_def.get("auto_demote", {})
        if not auto_demote.get("enabled"):
            continue

        cooldown = auto_demote.get("cooldown_hours", 0)
        if cooldown <= 0:
            continue

        target_severity = rule_def.get("target_severity", {})
        if not target_severity:
            continue

        for target, severity in list(target_severity.items()):
            if severity != "error":
                continue

            last = last_seen.get(rule_name, {}).get(target)
            if last and last >= now - timedelta(hours=cooldown):
                continue  # 最近出ている → 降格しない

            # 降格
            print(f"[DEMOTE] {rule_name}: {target} → warning")
            target_severity[target] = "warning"
            demoted = True

    if demoted:
        save_rules(rules)
        print("\n✅ rules.yaml updated (auto demote)")
    else:
        print("\n(no demotions applied)")

if __name__ == "__main__":
    main()
