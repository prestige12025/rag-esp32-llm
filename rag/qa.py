# rag/qa.py
def build_prompt(question: str, contexts: list[dict]) -> str:
    context_text = "\n\n".join(
        f"[{c['source']} / chunk {c['chunk_index']}]\n{c['text']}"
        for c in contexts
    )

    return f"""
あなたは社内技術ナレッジAIです。
以下の情報のみを根拠に回答してください。

### 参考情報
{context_text}

### 質問
{question}

### 回答（根拠が分かるように簡潔に）
"""

def answer_with_llm(question: str, contexts: list[dict], llm_call):
    prompt = build_prompt(question, contexts)
    return llm_call(prompt)
