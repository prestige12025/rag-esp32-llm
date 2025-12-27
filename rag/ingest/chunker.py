# rag/ingest/chunker.py

def chunk_text(text, max_chars=500):
    """
    文章を段落ごとに分割し、max_chars ごとにチャンク化
    """
    paragraphs = text.split("\n")
    chunks = []
    current_chunk = ""
    chunk_id = 0

    for p in paragraphs:
        p = p.strip()
        if not p:
            continue

        if len(current_chunk) + len(p) + 1 > max_chars:
            chunks.append({"text": current_chunk, "chunk_id": chunk_id})
            chunk_id += 1
            current_chunk = p
        else:
            if current_chunk:
                current_chunk += "\n" + p
            else:
                current_chunk = p

    if current_chunk:
        chunks.append({"text": current_chunk, "chunk_id": chunk_id})

    return chunks
