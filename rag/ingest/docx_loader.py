# rag/ingest/docx_loader.py
from docx import Document

def load_docx_text(path):
    """
    DOCX ファイルから本文テキストを抽出
    """
    doc = Document(path)
    lines = []

    for p in doc.paragraphs:
        text = p.text.strip()
        if text:
            lines.append(text)

    return "\n".join(lines)
