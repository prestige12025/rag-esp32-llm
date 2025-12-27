# rag/retriever.py
from rag.vector_store import get_collection

def retrieve_chunks(query: str, top_k: int = 5):
    collection = get_collection()

    result = collection.query(
        query_texts=[query],
        n_results=top_k,
    )

    chunks = []
    for text, meta in zip(result["documents"][0], result["metadatas"][0]):
        chunks.append({
            "text": text,
            "source": meta.get("source"),
            "chunk_index": meta.get("chunk_index"),
        })

    return chunks
