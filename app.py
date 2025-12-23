# app.py
import os
import sys

# =====================
# pytest / CI safety
# =====================
IS_PYTEST = "pytest" in sys.modules

# =====================
# validate exports (pytest がここを見る)
# =====================
from validate import (
    VALIDATE_MAP,
    detect_rule_key,
    validate_common,
    validate_i2c,
    validate_spi,
    validate_i2c_spi,
    validate_default,
)

# =====================
# Streamlit / LangChain
# =====================
if not IS_PYTEST:
    import streamlit as st
    from langchain_community.document_loaders import TextLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_community.vectorstores import FAISS
    from langchain_ollama import OllamaLLM, OllamaEmbeddings


# =====================
# 設定
# =====================
DATA_DIR = "data/esp32"
RULE_DIR = "data/rules"
GOOD_DIR = "data/good_examples"

INDEX_DIR = "faiss_index"
RULE_INDEX_DIR = "faiss_rules"
GOOD_INDEX_DIR = "faiss_good"

EMBED_MODEL = "nomic-embed-text"
LLM_MODEL = "qwen2.5-coder:7b-instruct"
OLLAMA_URL = "http://127.0.0.1:11434"

MAX_QUERY_LEN = 400
MAX_INTERNAL_LEN = 1200
MAX_RETRY = 2

GOOD_RANKS = ["official", "recommended", "reference"]


# =====================
# Loader（CIでは未使用）
# =====================
def load_docs(path: str):
    if IS_PYTEST:
        return []
    docs = []
    if not os.path.exists(path):
        return docs
    for f in os.listdir(path):
        if f.endswith(".md") or f.endswith(".txt"):
            docs.extend(
                TextLoader(
                    os.path.join(path, f),
                    encoding="utf-8"
                ).load()
            )
    return docs


def build_store(docs, index_dir, embeddings):
    if IS_PYTEST or not docs:
        return None
    if os.path.exists(index_dir):
        return FAISS.load_local(
            index_dir,
            embeddings,
            allow_dangerous_deserialization=True
        )
    store = FAISS.from_documents(docs, embeddings)
    store.save_local(index_dir)
    return store


# =====================
# Streamlit main
# =====================
def main():
    if IS_PYTEST:
        return  # ← pytest では UI を一切起動しない

    st.set_page_config(page_title="社内LLMナレッジ", layout="wide")
    st.title("社内技術ナレッジAI（ESP32）")

    mode = st.radio(
        "利用目的を選択してください",
        ["質問・調査（RAG）", "Good例管理"],
        horizontal=True
    )

    for k in ["question", "last_answer", "clear_question", "force_good_example"]:
        st.session_state.setdefault(k, "")

    if st.session_state.clear_question:
        st.session_state.question = ""
        st.session_state.clear_question = False

    embeddings = OllamaEmbeddings(
        model=EMBED_MODEL,
        base_url=OLLAMA_URL
    )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=100
    )

    tech_docs = splitter.split_documents(load_docs(DATA_DIR))
    tech_store = build_store(tech_docs, INDEX_DIR, embeddings)
    tech_retriever = tech_store.as_retriever(search_kwargs={"k": 3}) if tech_store else None

    rule_docs = splitter.split_documents(load_docs(RULE_DIR))
    rule_store = build_store(rule_docs, RULE_INDEX_DIR, embeddings)

    def load_good_store():
        docs = splitter.split_documents(load_docs(GOOD_DIR))
        return build_store(docs, GOOD_INDEX_DIR, embeddings)

    good_store = load_good_store()

    llm = OllamaLLM(
        model=LLM_MODEL,
        base_url=OLLAMA_URL,
        temperature=0,
        timeout=30
    )

    if mode == "質問・調査（RAG）":
        st.text_area("質問内容", height=120, key="question")

        if st.button("実行") and st.session_state.question.strip():
            q = st.session_state.question
            rule_key = detect_rule_key(q)

            tech = (
                "\n".join(d.page_content for d in tech_retriever.invoke(q[:MAX_QUERY_LEN]))
                if tech_retriever else ""
            )[:MAX_INTERNAL_LEN]

            rules = (
                "\n".join(d.page_content for d in rule_store.similarity_search(rule_key, k=3))
                if rule_store else ""
            )

            good = (
                "\n".join(d.page_content for d in good_store.similarity_search(q, k=2))
                if good_store else ""
            )

            base_prompt = f"""
あなたはESP32専用コード生成AIです。

【必須ルール】
{rules}

【良い実装例】
{good}
{st.session_state.force_good_example}

【出力形式】
- ```cpp``` コードブロックのみ
- 説明文禁止

【社内技術文書】
{tech}

【質問】
{q}
"""

            validator = VALIDATE_MAP.get(rule_key, validate_default)
            answer = ""
            errors = []

            for _ in range(MAX_RETRY + 1):
                answer = llm.invoke(base_prompt)
                errors = validator(answer)
                if not errors:
                    break
                base_prompt += "\n【修正指示】\n" + "\n".join(errors)

            st.session_state.last_answer = answer
            st.session_state.clear_question = True
            st.rerun()

        if st.session_state.last_answer:
            st.markdown(st.session_state.last_answer)


# =====================
# entry point
# =====================
if __name__ == "__main__":
    main()
