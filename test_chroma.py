import chromadb
from chromadb.config import Settings

client = chromadb.Client(
    Settings(persist_directory="C:/ollama/rag/chroma")
)

col = client.get_or_create_collection("test_collection")

col.add(
    documents=["これは ChromaDB 永続化テストです"],
    ids=["test-1"],
    metadatas=[{"source": "test"}],
)

print("done")
