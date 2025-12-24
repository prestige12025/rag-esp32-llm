import re
from typing import Callable

# =====================
# Utilities
# =====================

def strip_comments(text: str) -> str:
    """C/C++ style comments を除去"""
    # // コメント
    text = re.sub(r"//.*", "", text)
    # /* */ コメント
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return text


# =====================
# 共通 validator
# =====================

def validate_common(text: str) -> list[str]:
    errs = []
    if "```cpp" not in text:
        errs.append("cppコードブロックのみ出力してください")
    if "#include <Arduino.h>" not in text:
        errs.append("Arduino.h は必須です")
    return errs


# =====================
# rule-specific validators
# =====================

def validate_i2c(text: str) -> list[str]:
    errs = validate_common(text)
    clean = strip_comments(text)

    for c in [
        "#include <Wire.h>",
        "Wire.begin()",
        "Wire.requestFrom",
        "Wire.available()",
    ]:
        if c not in clean:
            errs.append(f"{c} が不足しています")
    return errs


def validate_spi(text: str) -> list[str]:
    errs = validate_common(text)
    clean = strip_comments(text)

    for c in [
        "#include <SPI.h>",
        "SPI.begin()",
        "SPI.beginTransaction",
        "SPI.endTransaction",
    ]:
        if c not in clean:
            errs.append(f"{c} が不足しています")
    return errs


def validate_i2c_spi(text: str) -> list[str]:
    errs = validate_common(text)
    clean = strip_comments(text)

    for c in [
        "#include <Wire.h>",
        "#include <SPI.h>",
        "Wire.begin()",
        "SPI.begin()",
    ]:
        if c not in clean:
            errs.append(f"{c} が不足しています")
    return errs


def validate_default(text: str) -> list[str]:
    return validate_common(text)


# =====================
# Rule definition (single source of truth)
# =====================

RULES: dict[str, dict] = {
    "i2c_spi": {
        "keywords": ["i2c", "spi"],
        "validator": validate_i2c_spi,
    },
    "i2c": {
        "keywords": ["i2c"],
        "validator": validate_i2c,
    },
    "spi": {
        "keywords": ["spi"],
        "validator": validate_spi,
    },
    "default": {
        "keywords": [],
        "validator": validate_default,
    },
}


# =====================
# Public maps (app.py / pytest 用)
# =====================

VALIDATE_MAP: dict[str, Callable[[str], list[str]]] = {
    k: v["validator"] for k, v in RULES.items()
}


def detect_rule_key(q: str) -> str:
    """
    キーワード数が多いルールを優先して判定する
    """
    q = q.lower()

    # keywords 数が多い順に評価
    sorted_rules = sorted(
        RULES.items(),
        key=lambda item: len(item[1]["keywords"]),
        reverse=True,
    )

    for key, rule in sorted_rules:
        if all(kw in q for kw in rule["keywords"]):
            return key

    return "default"
