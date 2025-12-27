# rag/ingest/vectorize.py
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

# Embedding モデル
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"

def embed_chunks(chunks):
    """
    chunks = [{"text": ..., "meta": {...}}, ...]
    """
    model = SentenceTransformer(EMBED_MODEL_NAME)
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    return embeddings

def store_in_chroma(chunks, embeddings, collection_name="contracts"):
    client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory="./chroma_db"))
    if collection_name in [c.name for c in client.list_collections()]:
        collection = client.get_collection(name=collection_name)
    else:
        collection = client.create_collection(name=collection_name)

    # ID は path + chunk_id
    ids = [f"{c['meta']['path']}_{c['chunk_id']}" for c in chunks]

    collection.add(
        ids=ids,
        documents=[c["text"] for c in chunks],
        metadatas=[c["meta"] for c in chunks],
        embeddings=embeddings.tolist()
    )

    # 永続化
    client.persist()
