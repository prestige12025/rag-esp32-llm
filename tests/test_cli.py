# tests/test_cli.py
import subprocess
import sys
from pathlib import Path
import json

PYTHON = sys.executable
BASE_CMD = [PYTHON, "-m", "rag"]

DATA_DIR = Path("tests/data")


def run_cli(args):
    """
    CLI 実行ヘルパー
    """
    return subprocess.run(
        BASE_CMD + args,
        capture_output=True,
        text=True,
    )


def test_cli_ok_default():
    result = run_cli([str(DATA_DIR / "valid_i2c_spi.txt")])
    assert result.returncode == 0
    assert "[OK] validation passed" in result.stdout


def test_cli_ng_exit_code():
    result = run_cli([str(DATA_DIR / "invalid_no_wire_begin.txt")])
    assert result.returncode == 1
    assert "[NG]" in result.stdout


def test_cli_json_ok():
    result = run_cli(
        [str(DATA_DIR / "valid_i2c_spi.txt"), "--json"]
    )
    assert result.returncode == 0

    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    assert payload["errors"] == []
    assert "rule" in payload


def test_cli_json_ng():
    result = run_cli(
        [str(DATA_DIR / "invalid_no_wire_begin.txt"), "--json"]
    )
    assert result.returncode == 1

    payload = json.loads(result.stdout)
    assert payload["status"] == "ng"
    assert payload["errors"]
    assert isinstance(payload["errors"], list)


def test_cli_quiet_ok():
    result = run_cli(
        [str(DATA_DIR / "valid_i2c_spi.txt"), "--quiet"]
    )
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_cli_verbose_ok():
    result = run_cli(
        [str(DATA_DIR / "valid_i2c_spi.txt"), "--verbose"]
    )
    assert result.returncode == 0
    assert "[INFO] detected rule:" in result.stdout
    assert "[OK] validation passed" in result.stdout


def test_cli_unknown_rule():
    result = run_cli(
        [str(DATA_DIR / "valid_i2c_spi.txt"), "--rule", "unknown"]
    )
    assert result.returncode == 2
    assert "unknown rule" in result.stderr.lower()
