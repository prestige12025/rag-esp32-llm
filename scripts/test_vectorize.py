# scripts/test_vectorize.py
from pathlib import Path
from rag.ingest.loader import load_documents
from rag.ingest.docx_loader import load_docx_text
from rag.ingest.chunker import chunk_text
from rag.ingest.vectorize import embed_chunks, store_in_chroma

BASE = Path(
    r"\\192.168.11.66\Public\社内共有\機械警備関係\書類\契約書"
)

docs = load_documents(BASE)
docx_docs = [d for d in docs if d["ext"] == ".docx"]

sample = docx_docs[0]
text = load_docx_text(sample["path"])
chunks = chunk_text(text, max_chars=500)

embeddings = embed_chunks(chunks)
store_in_chroma(chunks, embeddings)

print("Embedding + Chroma 保存 完了")
