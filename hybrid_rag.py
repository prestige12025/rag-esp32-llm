import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_community.tools import DuckDuckGoSearchRun

# ========= 設定 =========
DATA_DIR = "data"
INDEX_DIR = "faiss_index"
EMBED_MODEL = "nomic-embed-text"
LLM_MODEL = "codellama:7b-instruct"
OLLAMA_URL = "http://127.0.0.1:11434"

# ========= Embedding =========
embeddings = OllamaEmbeddings(
    model=EMBED_MODEL,
    base_url=OLLAMA_URL
)

# ========= 社内文書ロード =========
def load_docs(subdir):
    docs = []
    base = os.path.join(DATA_DIR, subdir)
    if not os.path.exists(base):
        return docs

    for file in os.listdir(base):
        if file.endswith(".md"):
            loader = TextLoader(os.path.join(base, file), encoding="utf-8")
            docs.extend(loader.load())
    return docs

esp32_docs = load_docs("esp32")
llm_docs   = load_docs("llm")
rule_docs  = load_docs("rules")

all_docs = esp32_docs + llm_docs + rule_docs

print("=== 読み込まれた社内文書 ===")
for d in all_docs:
    print(d.metadata["source"])
print("==========================")

# ========= 分割 =========
splitter = RecursiveCharacterTextSplitter(
    chunk_size=600,
    chunk_overlap=80
)
docs = splitter.split_documents(all_docs)

# ========= FAISS =========
if os.path.exists(INDEX_DIR):
    print("=== FAISS インデックスをロード ===")
    vectorstore = FAISS.load_local(
        INDEX_DIR, embeddings, allow_dangerous_deserialization=True
    )
else:
    print("=== FAISS インデックスを新規作成 ===")
    vectorstore = FAISS.from_documents(docs, embeddings)
    vectorstore.save_local(INDEX_DIR)
    print("=== FAISS インデックスを保存 ===")

retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

# ========= Web検索 =========
search = DuckDuckGoSearchRun()

# ========= LLM =========
llm = OllamaLLM(
    model=LLM_MODEL,
    base_url=OLLAMA_URL,
    temperature=0.2
)

# ========= 質問 =========
question = input("\n質問を入力してください: ")

q = question.lower()

# ========= ジャンル判定 =========
if any(k in q for k in ["esp32", "ledc", "gpio", "arduino"]):
    domain = "ESP32"
elif any(k in q for k in ["ollama", "rag", "llm", "faiss", "streamlit"]):
    domain = "LLM"
else:
    domain = "GENERAL"

# ========= 社内文書検索 =========
internal_docs = retriever.get_relevant_documents(question)
internal_text = "\n".join([d.page_content for d in internal_docs])

# ========= Web検索（補助） =========
try:
    web_text = search.run(question)
except Exception:
    web_text = "（Web検索失敗）"

# ========= 統合プロンプト =========
prompt = f"""
あなたは社内向け技術標準を回答するAIです。
一般論や推測は禁止します。

【対象領域】
{domain}

【社内文書（最優先）】
{internal_text}

【Web検索（補助情報）】
{web_text}

【質問】
{question}

【制約】
- 社内文書にない内容は「社内未定義」と明示
- 再現可能な手順のみ記載
- 必要に応じて注意点を箇条書き
"""

# ========= 実行 =========
response = llm.invoke(prompt)

print("\n=== 回答 ===\n")
print(response)
