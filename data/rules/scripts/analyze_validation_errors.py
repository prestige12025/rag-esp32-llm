# scripts/analyze_validation_errors.py
import json
from collections import Counter, defaultdict
from pathlib import Path

LOG_PATH = Path("logs/validation_errors.jsonl")
OUT_PATH = Path("logs/rule_candidates.md")

MIN_COUNT = 2  # 何回以上出たら「ルール化候補」か


def load_errors():
    records = []
    if not LOG_PATH.exists():
        return records

    with LOG_PATH.open(encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))
    return records


def analyze(records):
    counter = Counter()
    by_rule = defaultdict(list)

    for r in records:
        rule = r["rule"]
        for e in r["errors"]:
            msg = e.get("message", "").strip()
            if msg:
                counter[msg] += 1
                by_rule[rule].append(msg)

    return counter, by_rule


def generate_markdown(counter, by_rule):
    lines = []
    lines.append("# 自動生成ルール候補\n")

    for msg, count in counter.most_common():
        if count < MIN_COUNT:
            continue

        lines.append(f"## ❗ {msg}")
        lines.append(f"- 発生回数: **{count}回**")

        related_rules = [
            rule for rule, msgs in by_rule.items() if msg in msgs
        ]
        if related_rules:
            lines.append(f"- 関連ルールキー: `{', '.join(set(related_rules))}`")

        lines.append("")
        lines.append("### 🔧 ルール案")
        lines.append(f"- {msg} を必須とする")
        lines.append("")
        lines.append("---\n")

    return "\n".join(lines)


def main():
    records = load_errors()
    if not records:
        print("No validation errors found.")
        return

    counter, by_rule = analyze(records)
    md = generate_markdown(counter, by_rule)

    OUT_PATH.write_text(md, encoding="utf-8")
    print(f"Rule candidates written to {OUT_PATH}")


if __name__ == "__main__":
    main()
