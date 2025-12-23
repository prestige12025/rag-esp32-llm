# validate.py
import re


# =====================
# 用途判定
# =====================
def detect_rule_key(q: str) -> str:
    q = q.lower()
    if "i2c" in q and "spi" in q:
        return "i2c_spi"
    if "i2c" in q:
        return "i2c"
    if "spi" in q:
        return "spi"
    return "default"


# =====================
# validate 共通
# =====================
def validate_common(text: str) -> list[str]:
    errors = []

    if not re.search(r"```cpp[\s\S]*?```", text):
        errors.append("cppコードブロックのみ出力してください")

    if "#include <Arduino.h>" not in text:
        errors.append("Arduino.h は必須です")

    return errors


def validate_i2c_spi(text: str) -> list[str]:
    errors = validate_common(text)
    required = [
        "#include <Wire.h>",
        "#include <SPI.h>",
        "Wire.begin",
        "SPI.begin",
        "SPI.beginTransaction",
        "SPI.endTransaction",
    ]
    for r in required:
        if r not in text:
            errors.append(f"{r} が不足しています")
    return errors


def validate_i2c(text: str) -> list[str]:
    errors = validate_common(text)
    required = [
        "#include <Wire.h>",
        "Wire.begin",
        "Wire.requestFrom",
        "Wire.available",
    ]
    for r in required:
        if r not in text:
            errors.append(f"{r} が不足しています")
    return errors


def validate_spi(text: str) -> list[str]:
    errors = validate_common(text)
    required = [
        "#include <SPI.h>",
        "SPI.begin",
        "SPI.beginTransaction",
        "SPI.endTransaction",
    ]
    for r in required:
        if r not in text:
            errors.append(f"{r} が不足しています")
    return errors


def validate_default(text: str) -> list[str]:
    return validate_common(text)


# =====================
# ★ app.py から import される本体
# =====================
VALIDATE_MAP = {
    "i2c_spi": validate_i2c_spi,
    "i2c": validate_i2c,
    "spi": validate_spi,
    "default": validate_default,
}
