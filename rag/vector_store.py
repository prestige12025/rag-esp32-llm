from pathlib import Path
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

VECTOR_DIR = Path("data/vector")
VECTOR_DIR.mkdir(parents=True, exist_ok=True)

INDEX_PATH = VECTOR_DIR / "faiss.index"
META_PATH = VECTOR_DIR / "meta.json"

_model = SentenceTransformer("all-MiniLM-L6-v2")
_dim = 384

def _load_index():
    if INDEX_PATH.exists():
        return faiss.read_index(str(INDEX_PATH))
    return faiss.IndexFlatL2(_dim)

def _load_meta():
    if META_PATH.exists():
        return json.loads(META_PATH.read_text(encoding="utf-8"))
    return []

def _save(index, meta):
    faiss.write_index(index, str(INDEX_PATH))
    META_PATH.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def add_chunk(text: str, source: str, chunk_index: int):
    index = _load_index()
    meta = _load_meta()

    vec = _model.encode([text]).astype("float32")
    index.add(vec)

    meta.append({
        "source": source,
        "chunk_index": chunk_index,
        "text": text,
    })

    _save(index, meta)

def search(query: str, k: int = 5):
    if not INDEX_PATH.exists():
        return []

    index = _load_index()
    meta = _load_meta()

    q = _model.encode([query]).astype("float32")
    _, ids = index.search(q, k)

    return [meta[i] for i in ids[0] if i < len(meta)]
