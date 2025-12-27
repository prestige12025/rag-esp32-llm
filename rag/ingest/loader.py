# rag/ingest/loader.py
from pathlib import Path

# 今回 ingest 対象とする拡張子
SUPPORTED_EXTS = {".pdf", ".docx", ".txt"}

# 明示的に除外
SKIP_EXTS = {".exe", ".lnk", ".jpg", ".jpeg", ".png", ".mp4", ".avi"}

def load_documents(base_path: Path):
    """
    契約書フォルダー配下を再帰的にスキャンし
    ingest 対象ファイルだけを収集する
    """
    if not base_path.exists():
        raise FileNotFoundError(base_path)

    docs = []

    for path in base_path.rglob("*"):
        if not path.is_file():
            continue

        ext = path.suffix.lower()

        if ext in SKIP_EXTS:
            continue

        if ext not in SUPPORTED_EXTS:
            continue

        docs.append(
            {
                "path": path,
                "ext": ext,
                "meta": {
                    "source": "nas",
                    "category": "contract",
                    "path": str(path),
                    "name": path.name,
                },
            }
        )

    return docs
