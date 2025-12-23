import streamlit as st
import os
import re

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_core.documents import Document

# =====================
# 設定
# =====================
DATA_DIR = "data/esp32"
RULE_DIR = "data/rules"
BAD_DIR = "data/bad_examples"
GOOD_DIR = "data/good_examples"

INDEX_DIR = "faiss_index"
RULE_INDEX_DIR = "faiss_rules"
BAD_INDEX_DIR = "faiss_bad"
GOOD_INDEX_DIR = "faiss_good"

EMBED_MODEL = "nomic-embed-text"
LLM_MODEL = "qwen2.5-coder:7b-instruct"
OLLAMA_URL = "http://127.0.0.1:11434"

MAX_QUERY_LEN = 400
MAX_INTERNAL_LEN = 1200
MAX_RETRY = 2

GOOD_RANKS = ["official", "recommended", "reference"]

# =====================
# UI
# =====================
st.set_page_config(page_title="社内LLMナレッジ", layout="wide")
st.title("社内技術ナレッジAI（ESP32）")

mode = st.radio(
    "利用目的を選択してください",
    ["質問・調査（RAG）", "Good例管理"],
    horizontal=True
)

# =====================
# Session State
# =====================
for k in ["question", "last_answer", "clear_question", "force_good_example"]:
    st.session_state.setdefault(k, "")

if st.session_state.clear_question:
    st.session_state.question = ""
    st.session_state.clear_question = False

# =====================
# Embedding
# =====================
embeddings = OllamaEmbeddings(
    model=EMBED_MODEL,
    base_url=OLLAMA_URL
)

# =====================
# Loader
# =====================
def load_docs(path):
    docs = []
    if not os.path.exists(path):
        return docs
    for f in os.listdir(path):
        if f.endswith(".md") or f.endswith(".txt"):
            docs.extend(TextLoader(os.path.join(path, f), encoding="utf-8").load())
    return docs

splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=100)

# =====================
# 社内技術RAG
# =====================
tech_docs = splitter.split_documents(load_docs(DATA_DIR))
tech_store = FAISS.from_documents(tech_docs, embeddings) if not os.path.exists(INDEX_DIR) \
    else FAISS.load_local(INDEX_DIR, embeddings, allow_dangerous_deserialization=True)
tech_store.save_local(INDEX_DIR)
tech_retriever = tech_store.as_retriever(search_kwargs={"k": 3})

# =====================
# ルールRAG
# =====================
rule_docs = splitter.split_documents(load_docs(RULE_DIR))
rule_store = FAISS.from_documents(rule_docs, embeddings) if rule_docs and not os.path.exists(RULE_INDEX_DIR) \
    else FAISS.load_local(RULE_INDEX_DIR, embeddings, allow_dangerous_deserialization=True) if os.path.exists(RULE_INDEX_DIR) else None
if rule_store:
    rule_store.save_local(RULE_INDEX_DIR)

# =====================
# Good例 RAG
# =====================
def load_good_store():
    docs = splitter.split_documents(load_docs(GOOD_DIR))
    if docs:
        store = FAISS.from_documents(docs, embeddings) if not os.path.exists(GOOD_INDEX_DIR) \
            else FAISS.load_local(GOOD_INDEX_DIR, embeddings, allow_dangerous_deserialization=True)
        store.save_local(GOOD_INDEX_DIR)
        return store
    return None

good_store = load_good_store()

# =====================
# LLM
# =====================
llm = OllamaLLM(
    model=LLM_MODEL,
    base_url=OLLAMA_URL,
    temperature=0,
    timeout=30
)

# =====================
# 用途判定
# =====================
def detect_rule_key(q: str) -> str:
    q = q.lower()
    if "i2c" in q and "spi" in q:
        return "i2c_spi"
    if "i2c" in q:
        return "i2c"
    if "spi" in q:
        return "spi"
    return "default"

# =====================
# validate（用途別）
# =====================
def validate_common(text: str) -> list[str]:
    errs = []
    if not re.search(r"```cpp[\s\S]*?```", text):
        errs.append("cppコードブロックのみ出力してください")
    if "#include <Arduino.h>" not in text:
        errs.append("Arduino.h は必須です")
    return errs

def validate_i2c_spi(text: str) -> list[str]:
    errs = validate_common(text)
    checks = [
        "#include <Wire.h>",
        "#include <SPI.h>",
        "Wire.begin()",
        "SPI.begin()",
        "SPI.beginTransaction",
        "SPI.endTransaction",
        "Wire.requestFrom",
        "Wire.available()",
        "digitalWrite"
    ]
    for c in checks:
        if c not in text:
            errs.append(f"{c} が不足しています")
    return errs

def validate_i2c(text: str) -> list[str]:
    errs = validate_common(text)
    for c in ["#include <Wire.h>", "Wire.begin()", "Wire.requestFrom", "Wire.available()"]:
        if c not in text:
            errs.append(f"{c} が不足しています")
    return errs

def validate_spi(text: str) -> list[str]:
    errs = validate_common(text)
    for c in ["#include <SPI.h>", "SPI.begin()", "SPI.beginTransaction", "SPI.endTransaction", "digitalWrite"]:
        if c not in text:
            errs.append(f"{c} が不足しています")
    return errs

def validate_default(text: str) -> list[str]:
    return validate_common(text)

VALIDATE_MAP = {
    "i2c_spi": validate_i2c_spi,
    "i2c": validate_i2c,
    "spi": validate_spi,
    "default": validate_default,
}

# =====================
# 質問・調査（RAG）
# =====================
if mode == "質問・調査（RAG）":

    st.text_area("質問内容", height=120, key="question")

    if st.button("実行") and st.session_state.question.strip():

        q = st.session_state.question
        rule_key = detect_rule_key(q)

        tech = "\n".join(d.page_content for d in tech_retriever.invoke(q[:MAX_QUERY_LEN]))[:MAX_INTERNAL_LEN]
        rules = "\n".join(d.page_content for d in rule_store.similarity_search(rule_key, k=3)) if rule_store else ""
        good = "\n".join(d.page_content for d in good_store.similarity_search(q, k=2)) if good_store else ""

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

        answer = ""
        errors = []

        validator = VALIDATE_MAP.get(rule_key, validate_default)

        for _ in range(MAX_RETRY + 1):
            answer = llm.invoke(base_prompt)
            errors = validator(answer)
            if not errors:
                break
            base_prompt += "\n【修正指示】\n" + "\n".join(errors)

        # --- Good 保存 ---
        if not errors:
            os.makedirs(GOOD_DIR, exist_ok=True)
            with open(os.path.join(GOOD_DIR, "reference.md"), "a", encoding="utf-8") as f:
                f.write(answer + "\n\n")
            good_store = load_good_store()

        st.session_state.last_answer = answer
        st.session_state.clear_question = True
        st.rerun()

    if st.session_state.last_answer:
        st.markdown(st.session_state.last_answer)

# =====================
# Good例管理
# =====================
elif mode == "Good例管理":

    st.subheader("Good例 一覧・管理")

    for rank in GOOD_RANKS:
        path = os.path.join(GOOD_DIR, f"{rank}.md")
        if not os.path.exists(path):
            continue

        st.markdown(f"## {rank.upper()}")
        content = open(path, encoding="utf-8").read().split("```cpp")

        for i, block in enumerate(content[1:], start=1):
            code = "```cpp" + block.split("```")[0] + "```"
            with st.expander(f"{rank} #{i}"):
                st.markdown(code)
                if st.button("再利用", key=f"use_{rank}_{i}"):
                    st.session_state.force_good_example = code
                    st.success("次回生成時に強制注入します")
