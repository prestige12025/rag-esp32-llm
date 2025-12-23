
from pathlib import Path

from app import (
    validate_common,
    validate_i2c_spi,
    validate_i2c,
    validate_spi,
    validate_default,
)

BASE = Path(__file__).parent / "data"

def load(name: str) -> str:
    return (BASE / name).read_text(encoding="utf-8")

def test_validate_common_ok():
    assert validate_common(load("valid_i2c_spi.txt")) == []

def test_validate_common_fail_no_block():
    errs = validate_common(load("invalid_no_code_block.txt"))
    assert "cppコードブロックのみ出力してください" in errs

def test_validate_i2c_spi_ok():
    assert validate_i2c_spi(load("valid_i2c_spi.txt")) == []

def test_validate_i2c_spi_missing_spi_begin():
    errs = validate_i2c_spi(load("invalid_no_spi_begin.txt"))
    assert any("SPI.begin()" in e for e in errs)

def test_validate_i2c_ok():
    assert validate_i2c(load("valid_i2c_spi.txt")) == []

def test_validate_spi_ok():
    assert validate_spi(load("valid_i2c_spi.txt")) == []

def test_validate_default():
    assert validate_default(load("valid_i2c_spi.txt")) == []
