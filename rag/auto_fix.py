from dataclasses import dataclass
from typing import List
from rag.chunk import Chunk
from rag.core import ValidationResult


@dataclass
class FixResult:
    chunk: Chunk
    original: str
    fixed: str
    reason: str


def should_fix(chunk: Chunk, errors: List[ValidationResult]) -> bool:
    """
    修正対象かどうか判定
    """
    if chunk.score < 0.6:
        return False

    for e in errors:
        if e.severity == "error":
            return True

    return False


def build_fix_prompt(chunk: Chunk, errors: List[ValidationResult]) -> str:
    """
    LLM 用プロンプト
    """
    error_text = "\n".join(f"- {e.message}" for e in errors)

    return f"""
あなたは社内技術文書の編集アシスタントです。

以下のテキストには問題があります。
内容は変えず、技術的に正確な形に修正してください。

【ルール違反】
{error_text}

【元のテキスト】
{chunk.text}

【条件】
- 意味を変えない
- 構造は保持
- 推測で情報を追加しない
- 日本語

【修正後テキスト】
""".strip()


def fix_chunk_with_llm(
    chunk: Chunk,
    errors: List[ValidationResult],
    llm_call
) -> FixResult:
    """
    llm_call(prompt: str) -> str を注入
    """
    prompt = build_fix_prompt(chunk, errors)
    fixed = llm_call(prompt)

    return FixResult(
        chunk=chunk,
        original=chunk.text,
        fixed=fixed.strip(),
        reason="; ".join(e.message for e in errors),
    )
