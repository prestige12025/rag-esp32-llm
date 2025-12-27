from pathlib import Path
from docx import Document
import chromadb
from sentence_transformers import SentenceTransformer

# =========================
# 設定
# =========================
DOCS_DIR = Path("data/docs")
CHROMA_PATH = "C:/ollama/rag/chroma"
COLLECTION_NAME = "docs_collection"

CHUNK_SIZE = 500
OVERLAP = 100

# =========================
# utils
# =========================
def load_docx(path: Path) -> str:
    doc = Document(path)
    lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n".join(lines)

def chunk_text(text: str):
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end])
        start = end - OVERLAP
    return chunks

# =========================
# main
# =========================
def main():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    model = SentenceTransformer("all-MiniLM-L6-v2")

    total_added = 0

    for docx_path in DOCS_DIR.glob("**/*.docx"):
        text = load_docx(docx_path)
        if not text.strip():
            continue

        chunks = chunk_text(text)
        embeddings = model.encode(chunks, show_progress_bar=False)

        ids = [f"{docx_path.stem}-{i}" for i in range(len(chunks))]

        # 既存ID除外（再実行安全）
        existing = set(collection.get(ids=ids)["ids"])
        new_items = [
            (i, chunks[i], embeddings[i])
            for i in range(len(ids))
            if ids[i] not in existing
        ]

        if not new_items:
            continue

        collection.add(
            documents=[x[1] for x in new_items],
            embeddings=[x[2] for x in new_items],
            ids=[ids[x[0]] for x in new_items],
            metadatas=[
                {
                    "source": docx_path.name,
                    "path": str(docx_path),
                    "chunk_id": x[0],
                }
                for x in new_items
            ],
        )

        total_added += len(new_items)
        print(f"✔ {docx_path.name}: +{len(new_items)}")

    print(f"\n=== DONE: added {total_added} chunks ===")

if __name__ == "__main__":
    main()
