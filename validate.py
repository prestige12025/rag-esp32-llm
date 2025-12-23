import re

FORBIDDEN_PHRASES = [
    "申し訳", "生成でき", "提供でき",
    "お応えでき", "困難", "理解でき"
]

def validate_answer(text: str, rule: str, gpio_dir: str) -> list[str]:
    errors = []

    # コードブロックを除外して日本語率チェック
    non_code = re.sub(r"```.*?```", "", text, flags=re.S)
    ascii_ratio = sum(1 for c in non_code if ord(c) < 128) / max(len(non_code), 1)
    if ascii_ratio > 0.4:
        errors.append("日本語のみで出力してください")

    # 謝罪・拒否の検出
    for p in FORBIDDEN_PHRASES:
        if p in text:
            errors.append("謝罪・拒否は禁止です。必ずコードを生成してください")
            break

    # Arduino.h 必須
    if "#include <Arduino.h>" not in text:
        errors.append("Arduino.h を include してください")

    return errors
