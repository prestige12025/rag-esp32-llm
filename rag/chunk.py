from dataclasses import dataclass
from typing import List


@dataclass
class Chunk:
    text: str
    index: int
    start: int
    end: int
    source: str      # ファイル名など
    score: float = 0.0  # ★ 重要度スコア（0.0〜1.0）


def score_chunk(text: str) -> float:
    """
    ルールベースの重要度スコア算出
    """
    t = text.lower()
    score = 0.0

    # -----------------
    # 情報量（長さ）
    # -----------------
    length = len(text)
    if length > 400:
        score += 0.3
    elif length > 200:
        score += 0.2
    else:
        score += 0.1

    # -----------------
    # 技術キーワード
    # -----------------
    keywords = [
        "i2c", "spi", "api", "register", "仕様",
        "parameter", "return", "example", "構成",
        "設計", "command", "interface"
    ]
    if any(k in t for k in keywords):
        score += 0.4

    # -----------------
    # 構造（箇条書き等）
    # -----------------
    if "\n-" in text or "\n*" in text or "\n•" in text:
        score += 0.1

    # -----------------
    # NG・弱情報
    # -----------------
    ng_words = ["todo", "未検証", "仮", "draft", "メモ"]
    if any(w in t for w in ng_words):
        score -= 0.2

    # 0.0〜1.0 に正規化
    return max(0.0, min(score, 1.0))


def split_text(
    text: str,
    source: str,
    chunk_size: int = 500,
    overlap: int = 100
) -> List[Chunk]:
    """
    テキストを chunk に分割し、重要度スコア付きで返す
    """
    chunks: List[Chunk] = []

    start = 0
    idx = 0
    length = len(text)

    while start < length:
        end = min(start + chunk_size, length)
        chunk_text = text[start:end]

        chunk = Chunk(
            text=chunk_text,
            index=idx,
            start=start,
            end=end,
            source=source,
            score=score_chunk(chunk_text),  # ★ ここで自動付与
        )

        chunks.append(chunk)

        idx += 1
        start += chunk_size - overlap

    return chunks
