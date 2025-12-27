from pathlib import Path
from datetime import datetime
import json
import yaml
import re
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

# =====================
# paths
# =====================
RULES_PATH = Path("data/rules/rules.yaml")
LOG_PATH = Path("logs/validation_errors.jsonl")
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

# =====================
# load rules
# =====================
def load_rules():
    if not RULES_PATH.exists():
        return {}
    with RULES_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

RULES = load_rules()

# =====================
# validation result
# =====================
@dataclass
class ValidationResult:
    ok: bool
    rule: str
    severity: str
    message: str
    fix_hint: Optional[str] = None

# =====================
# logging
# =====================
def log_validation_error(result: ValidationResult):
    rec = {
        "ts": datetime.utcnow().isoformat(),
        "rule": result.rule,
        "severity": result.severity,
        "message": result.message,
    }
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

# =====================
# helpers
# =====================
def _has_cpp_block(text: str) -> bool:
    return bool(re.search(r"```cpp[\s\S]*?```", text, re.IGNORECASE))


def _strip_cpp_comments(text: str) -> str:
    return re.sub(r"//.*", "", text)


def _has_wire_begin(text: str) -> bool:
    text = _strip_cpp_comments(text)
    return bool(re.search(r"\bwire\.begin\s*\(\s*\)", text, re.IGNORECASE))


def _has_spi_begin(text: str) -> bool:
    text = _strip_cpp_comments(text)
    return bool(re.search(r"\bspi\.begin\s*\(\s*\)", text, re.IGNORECASE))


def _extract_citations(text: str) -> List[str]:
    """
    [source: xxx] 形式の citation を抽出
    """
    return re.findall(r"\[source:\s*([^\]]+)\]", text)

# =====================
# common validator
# =====================
def validate_common(text: str, **context) -> List[ValidationResult]:
    results = []

    if not _has_cpp_block(text):
        results.append(
            ValidationResult(
                ok=False,
                rule="common_cpp_block",
                severity="error",
                message="cppコードブロックのみ出力してください",
                fix_hint="```cpp``` でコードを囲ってください",
            )
        )

    return results

# =====================
# rule-specific validators
# =====================
def validate_i2c(text: str, **context):
    results = validate_common(text)

    if not _has_wire_begin(text):
        results.append(
            ValidationResult(
                ok=False,
                rule="i2c",
                severity="error",
                message="Wire.begin() がありません",
                fix_hint="I2C 初期化コードを追加してください",
            )
        )
    return results


def validate_spi(text: str, **context):
    results = validate_common(text)

    if not _has_spi_begin(text):
        results.append(
            ValidationResult(
                ok=False,
                rule="spi",
                severity="error",
                message="SPI.begin() がありません",
                fix_hint="SPI 初期化コードを追加してください",
            )
        )
    return results


def validate_i2c_spi(text: str, **context):
    results = validate_common(text)

    if not _has_wire_begin(text):
        results.append(
            ValidationResult(
                ok=False,
                rule="i2c",
                severity="error",
                message="Wire.begin() がありません",
            )
        )
    if not _has_spi_begin(text):
        results.append(
            ValidationResult(
                ok=False,
                rule="spi",
                severity="error",
                message="SPI.begin() がありません",
            )
        )
    return results


def validate_default(text: str, **context):
    return validate_common(text)

# =====================
# RAG validators
# =====================
def validate_require_citation(text: str, **context):
    results = []
    citations = _extract_citations(text)

    if not citations:
        results.append(
            ValidationResult(
                ok=False,
                rule="require_citation",
                severity=RULES.get("require_citation", {}).get("severity", "error"),
                message="引用が含まれていません",
                fix_hint="[source: ドキュメント名#chunk_id] を追加してください",
            )
        )
    return results


def validate_rag_confidence(text: str, **context):
    results = []

    scores = context.get("rag_scores", [])
    threshold = RULES.get("rag_confidence", {}).get("threshold", 0.25)

    if not scores or max(scores) < threshold:
        results.append(
            ValidationResult(
                ok=False,
                rule="rag_confidence",
                severity=RULES.get("rag_confidence", {}).get("severity", "warning"),
                message="RAG 類似度が低すぎます",
                fix_hint="資料に基づかず、仕様不明として回答してください",
            )
        )
    return results

# =====================
# detect rule key
# =====================
def detect_rule_key(question: str) -> str:
    q = question.lower()
    has_i2c = "i2c" in q
    has_spi = "spi" in q

    if has_i2c and has_spi:
        return "i2c_spi"
    if has_i2c:
        return "i2c"
    if has_spi:
        return "spi"
    return "default"

# =====================
# VALIDATE MAP
# =====================
VALIDATE_MAP = {
    "default": validate_default,
    "i2c": validate_i2c,
    "spi": validate_spi,
    "i2c_spi": validate_i2c_spi,
    "require_citation": validate_require_citation,
    "rag_confidence": validate_rag_confidence,
}
