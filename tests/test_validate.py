from pathlib import Path
import pytest

from rag.validate import (
    RULES,
    VALIDATE_MAP,
    validate_common,
)

BASE = Path(__file__).parent / "data"


def load(name: str) -> str:
    return (BASE / name).read_text(encoding="utf-8")


# =====================
# common validator
# =====================

def test_validate_common_ok():
    assert validate_common(load("valid_i2c_spi.txt")) == []


def test_validate_common_fail_no_block():
    errs = validate_common(load("invalid_no_code_block.txt"))
    assert any(
        e.message == "cppコードブロックのみ出力してください"
        for e in errs
    )


# =====================
# rule-based validators
# =====================

@pytest.mark.parametrize("rule_key", RULES.keys())
def test_all_rules_have_validator(rule_key):
    assert rule_key in VALIDATE_MAP


@pytest.mark.parametrize("rule_key", RULES.keys())
def test_rule_valid_ok(rule_key):
    """
    valid_i2c_spi.txt は全ルールを満たす前提の万能サンプル
    """
    validator = VALIDATE_MAP[rule_key]
    assert validator(load("valid_i2c_spi.txt")) == []


@pytest.mark.parametrize(
    "rule_key, invalid_file, expected_missing",
    [
        ("i2c", "invalid_no_wire_begin.txt", "Wire.begin()"),
        ("spi", "invalid_no_spi_begin.txt", "SPI.begin()"),
        ("i2c_spi", "invalid_no_spi_begin.txt", "SPI.begin()"),
    ],
)
def test_rule_invalid_detects_missing(rule_key, invalid_file, expected_missing):
    validator = VALIDATE_MAP[rule_key]
    errs = validator(load(invalid_file))
    assert any(
        expected_missing in e.message
        for e in errs
    )
