# scripts/test_docx_text.py
from pathlib import Path
from rag.ingest.loader import load_documents
from rag.ingest.docx_loader import load_docx_text

BASE = Path(
    r"\\192.168.11.66\Public\社内共有\機械警備関係\書類\契約書"
)

docs = load_documents(BASE)

# DOCX のみ抽出
docx_docs = [d for d in docs if d["ext"] == ".docx"]

print(f"DOCX files: {len(docx_docs)}")

# サンプル1件を抽出
sample = docx_docs[0]
print("FILE:", sample["meta"]["path"])

text = load_docx_text(sample["path"])
print("TEXT SAMPLE (先頭1000文字):")
print(text[:1000])
