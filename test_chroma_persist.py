import chromadb

client = chromadb.PersistentClient(
    path="C:/ollama/rag/chroma"
)

col = client.get_or_create_collection("test_collection")

docs = [
    "これは ChromaDB の永続化テストです。",
    "ChromaDB は RAG 用のベクトルデータベースです。",
    "このコレクションは永続ストアに保存されます。",
]

col.add(
    documents=docs,
    ids=[f"id-{i}" for i in range(len(docs))],
    metadatas=[{"source": "test"}] * len(docs),
)

print("added:", col.count())
