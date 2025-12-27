import streamlit as st
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import difflib

from rag.validate import VALIDATE_MAP, validate_common
from rag.core import ValidationResult
from rag.chunk import split_text, Chunk
from rag.auto_fix import should_fix, fix_chunk_with_llm
from rag.fix_history import record_fix
from rag.vector_store import add_chunk
from rag.retriever import retrieve_chunks          # ★ 追加
from rag.qa import answer_with_llm                  # ★ 追加

# =====================
# Auto refresh (clock)
# =====================
st_autorefresh(interval=1000, key="clock_refresh")

# =====================
# rule key detection
# =====================
def detect_rule_key(text: str) -> str:
    t = text.lower()
    if "i2c" in t and "spi" in t:
        return "i2c_spi"
    if "i2c" in t:
        return "i2c"
    if "spi" in t:
        return "spi"
    return "default"

# =====================
# validator resolver
# =====================
def resolve_validators(rule_key: str):
    validators = []
    base = VALIDATE_MAP.get(rule_key)
    validators.append(base if callable(base) else validate_common)

    for k in ("require_citation", "rag_confidence"):
        v = VALIDATE_MAP.get(k)
        if callable(v):
            validators.append(v)

    return validators

# =====================
# validation (chunk-aware)
# =====================
def validate_chunk(chunk: Chunk):
    rule_key = detect_rule_key(chunk.text)
    validators = resolve_validators(rule_key)

    results: list[ValidationResult] = []
    for v in validators:
        results.extend(v(chunk.text))

    errors = [r for r in results if not r.ok and r.severity == "error"]
    return rule_key, errors

# =====================
# diff renderer
# =====================
def render_diff(original: str, fixed: str) -> str:
    diff = difflib.ndiff(
        original.splitlines(),
        fixed.splitlines()
    )

    rendered = []
    for line in diff:
        if line.startswith("- "):
            rendered.append(f"<span style='color:#d33'>- {line[2:]}</span>")
        elif line.startswith("+ "):
            rendered.append(f"<span style='color:#2a7'>+ {line[2:]}</span>")
        elif line.startswith("? "):
            continue
        else:
            rendered.append(line[2:])

    return "<br>".join(rendered)

# =====================
# LLM call（仮実装）
# =====================
def call_llm(prompt: str) -> str:
    return "【回答】\n" + prompt.split("### 質問")[-1].strip()

# =====================
# Streamlit UI
# =====================
st.set_page_config(page_title="社内技術ナレッジAI", layout="wide")
st.title("社内技術ナレッジAI")

now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
st.caption(f"🕒 現在時刻：{now}")
st.divider()

# =====================
# session state
# =====================
if "chunks" not in st.session_state:
    st.session_state.chunks = []

if "merged_text" not in st.session_state:
    st.session_state.merged_text = ""

# =====================
# File upload
# =====================
uploaded_files = st.file_uploader(
    "📂 ファイルをアップロード（複数可）",
    type=["txt", "md", "markdown"],
    accept_multiple_files=True
)

if uploaded_files:
    all_chunks = []
    merged = []

    for f in uploaded_files:
        text = f.read().decode("utf-8")
        merged.append(f"\n===== FILE: {f.name} =====\n{text}")

        all_chunks.extend(
            split_text(text=text, source=f.name)
        )

    st.session_state.chunks = all_chunks
    st.session_state.merged_text = "\n".join(merged)

# =====================
# Chunk-wise validation + auto-fix
# =====================
if st.session_state.chunks:
    st.subheader("🧩 チャンク単位検証結果")

    for i, chunk in enumerate(st.session_state.chunks):
        rule, errors = validate_chunk(chunk)

        # ---- OK → Vector DB 登録 ----
        if not errors:
            add_chunk(
                text=chunk.text,
                source=chunk.source,
                chunk_index=chunk.index,
            )
            continue

        with st.expander(
            f"❌ {chunk.source} / chunk #{chunk.index}（rule: {rule}）"
        ):
            st.code(chunk.text)

            for e in errors:
                st.error(str(e))

            if should_fix(chunk, errors):
                fix = fix_chunk_with_llm(
                    chunk=chunk,
                    errors=errors,
                    llm_call=call_llm,
                )

                st.markdown(
                    render_diff(chunk.text, fix.fixed),
                    unsafe_allow_html=True,
                )

                if st.button(
                    "✅ 修正を適用",
                    key=f"apply_{chunk.source}_{chunk.index}",
                ):
                    new_chunk = Chunk(
                        text=fix.fixed,
                        index=chunk.index,
                        start=chunk.start,
                        end=chunk.end,
                        source=chunk.source,
                    )

                    new_rule, new_errors = validate_chunk(new_chunk)

                    record_fix(
                        source=chunk.source,
                        chunk_index=chunk.index,
                        rule=new_rule,
                        errors_before=[str(e) for e in errors],
                        errors_after=[str(e) for e in new_errors],
                        original_text=chunk.text,
                        fixed_text=fix.fixed,
                    )

                    if not new_errors:
                        add_chunk(
                            text=new_chunk.text,
                            source=new_chunk.source,
                            chunk_index=new_chunk.index,
                        )

                        st.session_state.chunks[i] = new_chunk
                        st.session_state.merged_text = (
                            st.session_state.merged_text
                            .replace(chunk.text, fix.fixed, 1)
                        )
                        st.rerun()

    st.divider()

# =====================
# 質問（RAG QA）
# =====================
st.subheader("💬 ナレッジに質問")

question = st.text_input("質問を入力してください")

if question:
    with st.spinner("🔍 ナレッジ検索中..."):
        contexts = retrieve_chunks(question, top_k=5)

    if not contexts:
        st.warning("関連ナレッジが見つかりませんでした")
    else:
        answer = answer_with_llm(
            question=question,
            contexts=contexts,
            llm_call=call_llm,
        )

        st.markdown("### 🤖 回答")
        st.write(answer)

        st.markdown("### 📚 参照元")
        for c in contexts:
            st.caption(f"- {c['source']} / chunk {c['chunk_index']}")

# =====================
# Merged text
# =====================
st.text_area(
    "📄 統合テキスト（編集可）",
    height=300,
    key="merged_text"
)

# =====================
# Buttons
# =====================
col1, col2 = st.columns(2)

with col1:
    if st.button("🧹 クリア"):
        st.session_state.chunks = []
        st.session_state.merged_text = ""
        st.rerun()

with col2:
    if st.button("🔄 再読み込み"):
        st.rerun()
