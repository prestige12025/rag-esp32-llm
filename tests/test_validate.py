from pathlib import Path
import pytest

from app import (
    validate_common,
    validate_i2c,
    validate_spi,
    validate_i2c_spi,
    validate_default,
)

# =====================
# test data loader
# =====================

BASE = Path(__file__).parent / "data"

def load(name: str) -> str:
    return (BASE / name).read_text(encoding="utf-8")


# =====================
# validate_common
# =====================

def test_validate_common_ok():
    assert validate_common(load("valid_i2c_spi.txt")) == []


def test_validate_common_fail_no_block():
    errs = validate_common(load("invalid_no_code_block.txt"))
    assert "cppコードブロックのみ出力してください" in errs


# =====================
# rule-specific validators (parameterized)
# =====================

@pytest.mark.parametrize(
    "validator, valid_file, invalid_file, expected_missing",
    [
        (
            validate_i2c_spi,
            "valid_i2c_spi.txt",
            "invalid_no_spi_begin.txt",
            "SPI.begin()",
        ),
        (
            validate_i2c,
            "valid_i2c_spi.txt",
            "invalid_no_wire_begin.txt",
            "Wire.begin()",
        ),
        (
            validate_spi,
            "valid_i2c_spi.txt",
            "invalid_no_spi_begin.txt",
            "SPI.begin()",
        ),
    ],
)
def test_rule_validators(
    validator,
    valid_file,
    invalid_file,
    expected_missing,
):
    # 正常系
    assert validator(load(valid_file)) == []

    # 異常系
    errs = validator(load(invalid_file))
    assert any(expected_missing in e for e in errs)


# =====================
# default validator
# =====================

def test_validate_default():
    assert validate_default(load("valid_i2c_spi.txt")) == []
