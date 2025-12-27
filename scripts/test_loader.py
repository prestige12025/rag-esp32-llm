# scripts/test_loader.py
from pathlib import Path
from rag.ingest.loader import load_documents

BASE = Path(
    r"\\192.168.11.66\Public\社内共有\機械警備関係\書類\契約書"
)

docs = load_documents(BASE)

print(f"Detected documents: {len(docs)}")

# 拡張子別に集計
stats = {}
for d in docs:
    stats[d["ext"]] = stats.get(d["ext"], 0) + 1

print("Extension stats:")
for k, v in stats.items():
    print(f"  {k}: {v}")

print("\nSample files:")
for d in docs[:10]:
    print(f"{d['ext']}  {d['meta']['path']}")
