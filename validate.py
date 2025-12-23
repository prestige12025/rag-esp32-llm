import re

def detect_rule_key(q: str) -> str:
    q = q.lower()
    if "i2c" in q and "spi" in q:
        return "i2c_spi"
    if "i2c" in q:
        return "i2c"
    if "spi" in q:
        return "spi"
    return "default"


def validate_common(text: str) -> list[str]:
    errs = []
    if "```cpp" not in text:
        errs.append("cppコードブロックのみ出力してください")
    if "#include <Arduino.h>" not in text:
        errs.append("Arduino.h は必須です")
    return errs


def validate_i2c(text: str) -> list[str]:
    errs = validate_common(text)
    for c in ["#include <Wire.h>", "Wire.begin()", "Wire.requestFrom", "Wire.available()"]:
        if c not in text:
            errs.append(f"{c} が不足しています")
    return errs


def validate_spi(text: str) -> list[str]:
    errs = validate_common(text)
    for c in ["#include <SPI.h>", "SPI.begin()", "SPI.beginTransaction", "SPI.endTransaction"]:
        if c not in text:
            errs.append(f"{c} が不足しています")
    return errs


def validate_i2c_spi(text: str) -> list[str]:
    errs = validate_common(text)
    for c in [
        "#include <Wire.h>",
        "#include <SPI.h>",
        "Wire.begin()",
        "SPI.begin()",
    ]:
        if c not in text:
            errs.append(f"{c} が不足しています")
    return errs


def validate_default(text: str) -> list[str]:
    return validate_common(text)


VALIDATE_MAP = {
    "i2c": validate_i2c,
    "spi": validate_spi,
    "i2c_spi": validate_i2c_spi,
    "default": validate_default,
}
