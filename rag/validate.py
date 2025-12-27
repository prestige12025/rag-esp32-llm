# rag/validate.py
# 外部向け 公開APIラッパー
#
# 役割:
# - rag.core の実装を外部に公開するための安定API
# - テスト互換のため RULES を再エクスポート
# - 実装詳細（logging 等）には関与しない

from pathlib import Path
import yaml

# ★ 正解：同一パッケージ内の core を相対 import
from .core import (
    VALIDATE_MAP,
    validate_common,
    detect_rule_key,
)

# =====================
# rules.yaml 読み込み（参照専用）
# =====================
RULES_PATH = Path(__file__).parent / "data" / "rules" / "rules.yaml"


def load_rules():
    """
    rules.yaml を読み込む。
    validate.py では参照用途のみ。
    """
    if not RULES_PATH.exists():
        return {}
    with RULES_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


RULES = load_rules()

# =====================
# 公開API
# =====================
__all__ = [
    "RULES",
    "VALIDATE_MAP",
    "validate_common",
    "detect_rule_key",
]
